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
import { ApplicationsManager } from '@/components/admin/ApplicationsManager';
import { AuditLogViewer } from '@/components/admin/AuditLogViewer';
import { AdminStats } from '@/components/admin/AdminStats';
import { SecurityEvents } from '@/components/admin/SecurityEvents';
import { OrganisationManager } from '@/components/admin/OrganisationManager';
import UnifiedUserManagement from '@/components/admin/UnifiedUserManagement';
import { ErrorBoundary } from '@/components/ErrorBoundary';

// CRITICAL: Import auth debug utilities for Zebra Associates troubleshooting
import '@/utils/auth-debug';

type TabType = 'dashboard' | 'organisations' | 'applications' | 'user-management' | 'audit-logs' | 'security';

export default function AdminPage() {
  const { user, isLoading, isAuthenticated, isInitialized } = useAuthContext();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  // CRITICAL FIX: Enhanced user data validation and debugging for Matt.Lindop admin access
  const [debugInfo, setDebugInfo] = useState<string>('');

  useEffect(() => {
    // Enhanced debugging for admin access issues
    const debug = {
      isLoading,
      isAuthenticated,
      isInitialized,
      hasUser: !!user,
      userEmail: user?.email || 'N/A',
      userRole: user?.role || 'N/A',
      timestamp: new Date().toISOString()
    };

    const debugStr = `Auth State: ${JSON.stringify(debug, null, 2)}`;
    setDebugInfo(debugStr);
    console.log('🔍 MATT ADMIN ACCESS DEBUG:', debug);

    // More robust role checking - wait for initialization to complete
    if (isInitialized && user && user.role !== 'admin' && user.role !== 'super_admin') {
      console.log('🚨 ACCESS DENIED: User role insufficient', {
        email: user.email,
        role: user.role,
        requiredRoles: ['admin', 'super_admin']
      });
      window.location.href = '/dashboard';
    }
  }, [user, isLoading, isAuthenticated, isInitialized]);

  // CRITICAL DEBUG: Enhanced access control with detailed feedback for Zebra Associates troubleshooting
  // Wait for authentication to be fully initialized before making access decisions
  if (isLoading || !isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <h3 className="mt-2 text-lg font-medium text-gray-900">Loading...</h3>
          <p className="mt-1 text-sm text-gray-500">
            Verifying authentication and admin privileges...
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    console.log('🚨 Admin access denied: User not authenticated', { 
      isAuthenticated, 
      user: user ? { email: user.email, role: user.role } : null 
    });
    
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <ShieldCheckIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">Authentication Required</h3>
          <p className="mt-1 text-sm text-gray-500">
            Please log in to access the admin console.
          </p>
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-xs text-yellow-800">
              Debug: {isAuthenticated ? 'Authenticated but no user data' : 'Not authenticated'}
            </p>
            <p className="text-xs text-yellow-800 mt-1">
              If you should have access, try refreshing the page or logging in again.
            </p>
          </div>
          <button 
            onClick={() => router.push('/login')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  // CRITICAL FIX: Enhanced role validation for Matt.Lindop super_admin access
  const hasAdminAccess = user?.role === 'admin' || user?.role === 'super_admin';

  if (isInitialized && user && !hasAdminAccess) {
    console.log('🚨 Admin access denied: Insufficient privileges', {
      email: user.email,
      role: user.role,
      requiredRoles: ['admin', 'super_admin'],
      hasAdminAccess,
      isInitialized,
      debugInfo
    });

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <ShieldCheckIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">Access Denied</h3>
          <p className="mt-1 text-sm text-gray-500">
            You need administrator privileges to access this page.
          </p>
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-xs text-red-800">
              Current user: {user.email}
            </p>
            <p className="text-xs text-red-800 mt-1">
              Current role: {user.role} (Required: admin or super_admin)
            </p>
            <p className="text-xs text-red-800 mt-1">
              Has Admin Access: {hasAdminAccess ? 'YES' : 'NO'}
            </p>
            <p className="text-xs text-red-800 mt-1">
              Is Initialized: {isInitialized ? 'YES' : 'NO'}
            </p>
          </div>
          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
            <details className="text-left">
              <summary className="text-xs font-medium text-yellow-800 cursor-pointer">
                Debug Info (Click to expand)
              </summary>
              <pre className="text-xs text-yellow-700 mt-2 overflow-auto max-h-32">
                {debugInfo}
              </pre>
            </details>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // CRITICAL SUCCESS: Matt.Lindop has proper super_admin access!
  if (isInitialized && user && hasAdminAccess) {
    console.log('✅ ADMIN ACCESS GRANTED:', {
      email: user.email,
      role: user.role,
      hasAdminAccess,
      isInitialized,
      timestamp: new Date().toISOString()
    });
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
      description: 'Client management and configuration'
    },
    {
      id: 'applications',
      name: 'Applications',
      icon: CubeIcon,
      description: 'Manage apps and capabilities'
    },
    {
      id: 'user-management',
      name: 'User Management',
      icon: UsersIcon,
      description: 'Manage users and provisioning'
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
                <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                  user.role === 'super_admin'
                    ? 'bg-purple-100 text-purple-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {user.role === 'super_admin' ? 'Super Administrator' : 'Administrator'}
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
            {activeTab === 'dashboard' && (
              <ErrorBoundary componentName="AdminStats">
                <AdminStats />
              </ErrorBoundary>
            )}
            {activeTab === 'organisations' && (
              <ErrorBoundary componentName="OrganisationManager">
                <OrganisationManager />
              </ErrorBoundary>
            )}
            {activeTab === 'applications' && (
              <ErrorBoundary componentName="ApplicationsManager">
                <ApplicationsManager />
              </ErrorBoundary>
            )}
            {activeTab === 'user-management' && (
              <ErrorBoundary componentName="UnifiedUserManagement">
                <UnifiedUserManagement />
              </ErrorBoundary>
            )}
            {activeTab === 'audit-logs' && (
              <ErrorBoundary componentName="AuditLogViewer">
                <AuditLogViewer />
              </ErrorBoundary>
            )}
            {activeTab === 'security' && (
              <ErrorBoundary componentName="SecurityEvents">
                <SecurityEvents />
              </ErrorBoundary>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}