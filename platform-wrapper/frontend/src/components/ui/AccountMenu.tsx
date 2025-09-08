import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  UserCircleIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { useAuthContext } from '@/hooks/useAuth';
import { User } from '@/types/auth';

interface AccountMenuProps {
  className?: string;
}

export const AccountMenu: React.FC<AccountMenuProps> = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuthContext();
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    // Only add event listeners on client side
    if (typeof window !== 'undefined') {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, []);

  const handleLogout = () => {
    logout();
    setIsOpen(false);
  };

  // Check if user has admin role
  const isAdmin = user?.role === 'admin';

  if (!user) {
    return null;
  }

  return (
    <div className={`relative ${className}`} ref={menuRef}>
      {/* Account Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        <UserCircleIcon className="h-6 w-6" />
        <span className="hidden sm:block">{user.email}</span>
        <ChevronDownIcon className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
          <div className="py-1">
            {/* User Info Header */}
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-900">{user.email}</p>
              <p className="text-xs text-gray-500 capitalize">{user.role} • {user.organisation_id || 'No Organisation'}</p>
            </div>

            {/* Settings */}
            <button
              onClick={() => {
                // Navigate to settings page
                router.push('/settings');
                setIsOpen(false);
              }}
              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
            >
              <Cog6ToothIcon className="h-4 w-4 mr-3" />
              Settings
            </button>

            {/* Admin Panel (only show if user is admin) */}
            {isAdmin && (
              <button
                onClick={() => {
                  // Navigate to admin page
                  router.push('/admin');
                  setIsOpen(false);
                }}
                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              >
                <ShieldCheckIcon className="h-4 w-4 mr-3" />
                Admin Panel
              </button>
            )}

            {/* Divider */}
            <div className="border-t border-gray-100 my-1"></div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-red-50 hover:text-red-900"
            >
              <ArrowRightOnRectangleIcon className="h-4 w-4 mr-3" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};