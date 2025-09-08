'use client';

import React, { useState, useEffect } from 'react';
import {
  ShieldCheckIcon,
  CogIcon,
  FlagIcon,
  CubeIcon,
  UsersIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ClockIcon,
  BuildingOffice2Icon,
  ArrowLeftIcon,
  HomeIcon
} from '@heroicons/react/24/outline';
import { useAuthContext } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { FeatureFlagManager } from '@/components/admin/FeatureFlagManager';
import { ModuleManager } from '@/components/admin/ModuleManager';
import { EnhancedModuleManager } from '@/components/admin/EnhancedModuleManager';
import { AuditLogViewer } from '@/components/admin/AuditLogViewer';
import { AdminStats } from '@/components/admin/AdminStats';
import { SecurityEvents } from '@/components/admin/SecurityEvents';
import { OrganisationManager } from '@/components/admin/OrganisationManager';
import SuperAdminUserProvisioning from '@/components/admin/SuperAdminUserProvisioning';
import OrganizationUserManagement from '@/components/admin/OrganizationUserManagement';
import ApplicationAccessMatrix from '@/components/admin/ApplicationAccessMatrix';

type TabType = 'dashboard' | 'organisations' | 'user-provisioning' | 'user-management' | 'access-matrix' | 'feature-flags' | 'modules' | 'audit-logs' | 'security';

export default function AdminPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  // Redirect if not admin
  useEffect(() => {
    if (user && user.role !== 'admin') {
      window.location.href = '/dashboard';
    }
  }, [user]);

  if (!user || user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <ShieldCheckIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">Access Denied</h3>
          <p className="mt-1 text-sm text-gray-500">
            You need administrator privileges to access this page.
          </p>
        </div>
      </div>
    );
  }

  const tabs = [
    { 
      id: 'dashboard', 
      name: 'Dashboard', 
      icon: ChartBarIcon,
      description: 'Overview and statistics'
    },
    { 
      id: 'organisations', 
      name: 'Organisations', 
      icon: BuildingOffice2Icon,
      description: 'Create and manage organisations'
    },
    { 
      id: 'user-provisioning', 
      name: 'User Provisioning', 
      icon: UsersIcon,
      description: 'Create users across organizations'
    },
    { 
      id: 'user-management', 
      name: 'User Management', 
      icon: UsersIcon,
      description: 'Manage organization users'
    },
    { 
      id: 'access-matrix', 
      name: 'Access Matrix', 
      icon: CogIcon,
      description: 'Application access permissions'
    },
    { 
      id: 'feature-flags', 
      name: 'Feature Flags', 
      icon: FlagIcon,
      description: 'Manage feature rollouts'
    },
    { 
      id: 'modules', 
      name: 'Modules', 
      icon: CubeIcon,
      description: 'Analytics module management'
    },
    { 
      id: 'audit-logs', 
      name: 'Audit Logs', 
      icon: ClockIcon,
      description: 'System activity logs'
    },
    { 
      id: 'security', 
      name: 'Security', 
      icon: ExclamationTriangleIcon,
      description: 'Security events and alerts'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              {/* Return to Platform Button */}
              <button
                onClick={() => router.push('/dashboard')}
                className="group flex items-center mr-4 px-3 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200 border border-gray-200 hover:border-blue-300"
                title="Return to main platform"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2 group-hover:text-blue-600 transition-colors" />
                <HomeIcon className="h-4 w-4 mr-2 group-hover:text-blue-600 transition-colors" />
                <span className="hidden sm:inline">Return to Platform</span>
                <span className="sm:hidden">Platform</span>
              </button>

              <ShieldCheckIcon className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Admin Console</h1>
              <span className="ml-3 text-sm text-gray-500">Platform Management</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                <span className="font-medium text-gray-900">{user.email}</span>
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                  Administrator
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:w-64 flex-shrink-0">
            <nav className="space-y-2">

              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as TabType)}
                    className={`${
                      activeTab === tab.id
                        ? 'bg-blue-50 border-blue-500 text-blue-700'
                        : 'border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    } group flex items-start p-3 border-l-4 text-sm font-medium w-full text-left transition-colors`}
                  >
                    <Icon
                      className={`${
                        activeTab === tab.id ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                      } flex-shrink-0 mr-3 h-5 w-5`}
                    />
                    <div>
                      <div className="font-medium">{tab.name}</div>
                      <div className="text-xs text-gray-500 mt-1">{tab.description}</div>
                    </div>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {activeTab === 'dashboard' && <AdminStats />}
            {activeTab === 'organisations' && <OrganisationManager />}
            {activeTab === 'user-provisioning' && <SuperAdminUserProvisioning />}
            {activeTab === 'user-management' && <OrganizationUserManagement />}
            {activeTab === 'access-matrix' && <ApplicationAccessMatrix />}
            {activeTab === 'feature-flags' && <FeatureFlagManager />}
            {activeTab === 'modules' && <EnhancedModuleManager />}
            {activeTab === 'audit-logs' && <AuditLogViewer />}
            {activeTab === 'security' && <SecurityEvents />}
          </div>
        </div>
      </div>
    </div>
  );
}