/**
 * US-102: React Authentication Context Provider for Shared Authentication Context
 * 
 * Provides frontend integration with the enhanced authentication context system,
 * enabling cross-module authentication state sharing, session management,
 * and seamless navigation between modules.
 */

import React, { 
  createContext, 
  useContext, 
  useEffect, 
  useState, 
  useCallback, 
  useRef,
  ReactNode 
} from 'react';
import { useRouter } from 'next/navigation';

// Types for the authentication context
interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  organisation_id: string;
  is_active: boolean;
}

interface ModuleContext {
  [key: string]: any;
}

interface AuthContextState {
  // Core authentication data
  user: User | null;
  session_id: string | null;
  organisation_id: string | null;
  
  // Token and session management
  access_token: string | null;
  refresh_token: string | null;
  token_expires_at: Date | null;
  session_expires_at: Date | null;
  
  // Authorization data
  permissions: string[];
  roles: string[];
  module_access: Record<string, string>;
  
  // Session metadata
  created_at: Date | null;
  last_accessed_at: Date | null;
  last_module_accessed: string | null;
  access_count: number;
  
  // Cross-module data
  module_contexts: Record<string, ModuleContext>;
  shared_state: Record<string, any>;
  
  // Feature flags and preferences
  enabled_features: string[];
  user_preferences: Record<string, any>;
  
  // Loading and error states
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface AuthContextActions {
  // Authentication actions
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
  
  // Module context management
  setModuleContext: (moduleId: string, context: ModuleContext) => void;
  getModuleContext: (moduleId: string) => ModuleContext;
  clearModuleContext: (moduleId: string) => void;
  
  // Shared state management
  setSharedState: (key: string, value: any) => void;
  getSharedState: (key: string) => any;
  
  // Session management
  extendSession: () => Promise<boolean>;
  validateSession: () => Promise<boolean>;
  
  // Module access
  hasModuleAccess: (moduleId: string) => boolean;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  
  // Feature flags
  isFeatureEnabled: (featureKey: string) => boolean;
}

type AuthContextType = AuthContextState & AuthContextActions;

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Configuration
interface AuthContextProviderProps {
  children: ReactNode;
  apiBaseUrl?: string;
  sessionTimeoutMinutes?: number;
  tokenRefreshThresholdMinutes?: number;
  enableAutoRefresh?: boolean;
}

const DEFAULT_CONFIG = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || '/api',
  sessionTimeoutMinutes: 30,
  tokenRefreshThresholdMinutes: 15,
  enableAutoRefresh: true,
};

export function AuthContextProvider({
  children,
  apiBaseUrl = DEFAULT_CONFIG.apiBaseUrl,
  sessionTimeoutMinutes = DEFAULT_CONFIG.sessionTimeoutMinutes,
  tokenRefreshThresholdMinutes = DEFAULT_CONFIG.tokenRefreshThresholdMinutes,
  enableAutoRefresh = DEFAULT_CONFIG.enableAutoRefresh,
}: AuthContextProviderProps) {
  
  // State management
  const [state, setState] = useState<AuthContextState>({
    user: null,
    session_id: null,
    organisation_id: null,
    access_token: null,
    refresh_token: null,
    token_expires_at: null,
    session_expires_at: null,
    permissions: [],
    roles: [],
    module_access: {},
    created_at: null,
    last_accessed_at: null,
    last_module_accessed: null,
    access_count: 0,
    module_contexts: {},
    shared_state: {},
    enabled_features: [],
    user_preferences: {},
    isLoading: true,
    isAuthenticated: false,
    error: null,
  });
  
  const router = useRouter();
  const refreshTimeoutRef = useRef<NodeJS.Timeout>();
  const sessionCheckIntervalRef = useRef<NodeJS.Timeout>();
  
  // Initialize authentication state from localStorage
  useEffect(() => {
    initializeAuthState();
  }, []);
  
  // Set up auto-refresh and session monitoring
  useEffect(() => {
    if (state.isAuthenticated && enableAutoRefresh) {
      setupAutoRefresh();
      setupSessionMonitoring();
    }
    
    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
      if (sessionCheckIntervalRef.current) {
        clearInterval(sessionCheckIntervalRef.current);
      }
    };
  }, [state.isAuthenticated, state.token_expires_at]);
  
  const initializeAuthState = useCallback(async () => {
    try {
      // Try to load session from localStorage
      const storedSession = localStorage.getItem('auth_context');
      const storedTokens = localStorage.getItem('auth_tokens');
      
      if (storedSession && storedTokens) {
        const sessionData = JSON.parse(storedSession);
        const tokenData = JSON.parse(storedTokens);
        
        // Check if session is still valid
        const sessionExpiresAt = new Date(sessionData.session_expires_at);
        const tokenExpiresAt = new Date(tokenData.token_expires_at);
        const now = new Date();
        
        if (now < sessionExpiresAt && now < tokenExpiresAt) {
          // Validate session with backend
          const isValid = await validateSessionWithBackend(tokenData.access_token);
          if (isValid) {
            // Restore session state
            setState(prevState => ({
              ...prevState,
              ...sessionData,
              access_token: tokenData.access_token,
              refresh_token: tokenData.refresh_token,
              token_expires_at: tokenExpiresAt,
              session_expires_at: sessionExpiresAt,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            }));
            return;
          }
        }
      }
      
      // No valid session found
      clearAuthState();
      
    } catch (error) {
      console.error('Error initializing auth state:', error);
      clearAuthState();
    }
  }, []);
  
  const validateSessionWithBackend = async (token: string): Promise<boolean> => {
    try {
      const response = await fetch(`${apiBaseUrl}/v1/auth/validate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      return response.ok;
    } catch (error) {
      console.error('Session validation failed:', error);
      return false;
    }
  };
  
  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const response = await fetch(`${apiBaseUrl}/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }
      
      const data = await response.json();
      
      // Store tokens
      const tokenData = {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_expires_at: data.access_expires_at,
      };
      localStorage.setItem('auth_tokens', JSON.stringify(tokenData));
      
      // Get full authentication context
      const contextResponse = await fetch(`${apiBaseUrl}/v1/auth/context`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
          'X-Session-ID': data.session_id,
        },
      });
      
      if (!contextResponse.ok) {
        throw new Error('Failed to load authentication context');
      }
      
      const contextData = await contextResponse.json();
      
      // Update state with full context
      const newState = {
        ...contextData,
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_expires_at: new Date(data.access_expires_at),
        session_expires_at: new Date(contextData.session_expires_at),
        created_at: new Date(contextData.created_at),
        last_accessed_at: new Date(contextData.last_accessed_at),
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
      
      setState(prev => ({ ...prev, ...newState }));
      
      // Store session context
      localStorage.setItem('auth_context', JSON.stringify({
        ...contextData,
        session_expires_at: contextData.session_expires_at,
        created_at: contextData.created_at,
        last_accessed_at: contextData.last_accessed_at,
      }));
      
      return true;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
        isAuthenticated: false,
      }));
      return false;
    }
  }, [apiBaseUrl]);
  
  const logout = useCallback(async (): Promise<void> => {
    try {
      // Call logout endpoint if authenticated
      if (state.access_token) {
        await fetch(`${apiBaseUrl}/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${state.access_token}`,
            'X-Session-ID': state.session_id || '',
          },
        }).catch(console.error); // Don't fail logout if API call fails
      }
    } finally {
      clearAuthState();
      router.push('/login');
    }
  }, [state.access_token, state.session_id, apiBaseUrl, router]);
  
  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      if (!state.refresh_token) {
        return false;
      }
      
      const response = await fetch(`${apiBaseUrl}/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: state.refresh_token,
        }),
      });
      
      if (!response.ok) {
        return false;
      }
      
      const data = await response.json();
      
      // Update tokens
      const tokenData = {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_expires_at: data.access_expires_at,
      };
      localStorage.setItem('auth_tokens', JSON.stringify(tokenData));
      
      // Update state
      setState(prev => ({
        ...prev,
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_expires_at: new Date(data.access_expires_at),
        last_accessed_at: new Date(),
      }));
      
      return true;
      
    } catch (error) {
      console.error('Session refresh failed:', error);
      return false;
    }
  }, [state.refresh_token, apiBaseUrl]);
  
  const setupAutoRefresh = useCallback(() => {
    if (!state.token_expires_at) return;
    
    const now = new Date();
    const expirationTime = state.token_expires_at.getTime();
    const refreshTime = expirationTime - (tokenRefreshThresholdMinutes * 60 * 1000);
    const timeUntilRefresh = refreshTime - now.getTime();
    
    if (timeUntilRefresh > 0) {
      refreshTimeoutRef.current = setTimeout(async () => {
        const refreshed = await refreshSession();
        if (!refreshed) {
          // Refresh failed, logout user
          await logout();
        }
      }, timeUntilRefresh);
    }
  }, [state.token_expires_at, tokenRefreshThresholdMinutes, refreshSession, logout]);
  
  const setupSessionMonitoring = useCallback(() => {
    sessionCheckIntervalRef.current = setInterval(async () => {
      // Check for session timeout
      if (state.last_accessed_at) {
        const now = new Date();
        const timeoutThreshold = new Date(state.last_accessed_at.getTime() + (sessionTimeoutMinutes * 60 * 1000));
        
        if (now > timeoutThreshold) {
          console.log('Session timed out due to inactivity');
          await logout();
          return;
        }
      }
      
      // Validate session is still active
      if (state.access_token) {
        const isValid = await validateSessionWithBackend(state.access_token);
        if (!isValid) {
          console.log('Session validation failed');
          await logout();
        }
      }
    }, 5 * 60 * 1000); // Check every 5 minutes
  }, [state.last_accessed_at, state.access_token, sessionTimeoutMinutes, logout]);
  
  const clearAuthState = useCallback(() => {
    setState({
      user: null,
      session_id: null,
      organisation_id: null,
      access_token: null,
      refresh_token: null,
      token_expires_at: null,
      session_expires_at: null,
      permissions: [],
      roles: [],
      module_access: {},
      created_at: null,
      last_accessed_at: null,
      last_module_accessed: null,
      access_count: 0,
      module_contexts: {},
      shared_state: {},
      enabled_features: [],
      user_preferences: {},
      isLoading: false,
      isAuthenticated: false,
      error: null,
    });
    
    // Clear localStorage
    localStorage.removeItem('auth_context');
    localStorage.removeItem('auth_tokens');
  }, []);
  
  // Module context management
  const setModuleContext = useCallback((moduleId: string, context: ModuleContext) => {
    setState(prev => ({
      ...prev,
      module_contexts: {
        ...prev.module_contexts,
        [moduleId]: {
          ...context,
          updated_at: new Date().toISOString(),
        },
      },
      last_module_accessed: moduleId,
    }));
    
    // Persist to localStorage
    const updatedContext = {
      ...state,
      module_contexts: {
        ...state.module_contexts,
        [moduleId]: {
          ...context,
          updated_at: new Date().toISOString(),
        },
      },
    };
    localStorage.setItem('auth_context', JSON.stringify(updatedContext));
  }, [state]);
  
  const getModuleContext = useCallback((moduleId: string): ModuleContext => {
    return state.module_contexts[moduleId] || {};
  }, [state.module_contexts]);
  
  const clearModuleContext = useCallback((moduleId: string) => {
    setState(prev => {
      const { [moduleId]: removed, ...remaining } = prev.module_contexts;
      return {
        ...prev,
        module_contexts: remaining,
      };
    });
  }, []);
  
  // Shared state management
  const setSharedState = useCallback((key: string, value: any) => {
    setState(prev => ({
      ...prev,
      shared_state: {
        ...prev.shared_state,
        [key]: value,
      },
    }));
  }, []);
  
  const getSharedState = useCallback((key: string): any => {
    return state.shared_state[key];
  }, [state.shared_state]);
  
  // Session management
  const extendSession = useCallback(async (): Promise<boolean> => {
    try {
      if (!state.access_token || !state.session_id) {
        return false;
      }
      
      const response = await fetch(`${apiBaseUrl}/v1/auth/extend-session`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${state.access_token}`,
          'X-Session-ID': state.session_id,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setState(prev => ({
          ...prev,
          session_expires_at: new Date(data.session_expires_at),
          last_accessed_at: new Date(),
        }));
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Failed to extend session:', error);
      return false;
    }
  }, [state.access_token, state.session_id, apiBaseUrl]);
  
  const validateSession = useCallback(async (): Promise<boolean> => {
    if (!state.access_token) {
      return false;
    }
    return validateSessionWithBackend(state.access_token);
  }, [state.access_token]);
  
  // Access control methods
  const hasModuleAccess = useCallback((moduleId: string): boolean => {
    return state.module_access.hasOwnProperty(moduleId) && 
           state.module_access[moduleId] !== 'none';
  }, [state.module_access]);
  
  const hasPermission = useCallback((permission: string): boolean => {
    return state.permissions.includes(permission);
  }, [state.permissions]);
  
  const hasRole = useCallback((role: string): boolean => {
    return state.roles.includes(role);
  }, [state.roles]);
  
  const isFeatureEnabled = useCallback((featureKey: string): boolean => {
    return state.enabled_features.includes(featureKey);
  }, [state.enabled_features]);
  
  // Context value
  const contextValue: AuthContextType = {
    // State
    ...state,
    
    // Actions
    login,
    logout,
    refreshSession,
    setModuleContext,
    getModuleContext,
    clearModuleContext,
    setSharedState,
    getSharedState,
    extendSession,
    validateSession,
    hasModuleAccess,
    hasPermission,
    hasRole,
    isFeatureEnabled,
  };
  
  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use the auth context
export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthContextProvider');
  }
  return context;
}

// Hook for module-specific authentication
export function useModuleAuth(moduleId: string) {
  const authContext = useAuthContext();
  
  const hasAccess = authContext.hasModuleAccess(moduleId);
  const moduleContext = authContext.getModuleContext(moduleId);
  
  const setContext = useCallback((context: ModuleContext) => {
    authContext.setModuleContext(moduleId, context);
  }, [authContext, moduleId]);
  
  const clearContext = useCallback(() => {
    authContext.clearModuleContext(moduleId);
  }, [authContext, moduleId]);
  
  return {
    hasAccess,
    moduleContext,
    setContext,
    clearContext,
    isAuthenticated: authContext.isAuthenticated,
    user: authContext.user,
    permissions: authContext.permissions,
    roles: authContext.roles,
  };
}

// Higher-order component for module protection
export function withModuleAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  moduleId: string,
  requiredPermissions?: string[]
) {
  return function ModuleProtectedComponent(props: P) {
    const authContext = useAuthContext();
    const moduleAuth = useModuleAuth(moduleId);
    
    // Check authentication
    if (!authContext.isAuthenticated) {
      return <div>Please log in to access this module.</div>;
    }
    
    // Check module access
    if (!moduleAuth.hasAccess) {
      return <div>You don't have access to this module.</div>;
    }
    
    // Check required permissions
    if (requiredPermissions) {
      const hasRequiredPermissions = requiredPermissions.every(permission =>
        authContext.hasPermission(permission)
      );
      
      if (!hasRequiredPermissions) {
        return <div>You don't have sufficient permissions for this module.</div>;
      }
    }
    
    return <WrappedComponent {...props} />;
  };
}