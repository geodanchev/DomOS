import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User, UIPermissions } from '../types';
import { authApi } from '../services/api';

// =============================================================================
// Default permissions for viewer (most restrictive)
// =============================================================================
const DEFAULT_PERMISSIONS: UIPermissions = {
  apartments: { view: true, create: false, edit: false, delete: false },
  payments: { view: true, create: false, void: false },
  obligations: { view: true, create: false, edit: false, delete: false, generate_monthly: false },
  expenses: { view: true, create: false, edit: false, delete: false },
  reports: { view: true, export: true },
  scheduler: { manage: false },
  users: { manage: false },
};

// =============================================================================
// Auth Context Type
// =============================================================================
interface AuthContextType {
  user: User | null;
  token: string | null;
  permissions: UIPermissions;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// =============================================================================
// useAuth Hook
// =============================================================================
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// =============================================================================
// usePermissions Hook - convenient access to permissions
// =============================================================================
export const usePermissions = (): UIPermissions => {
  const { permissions } = useAuth();
  return permissions;
};

// =============================================================================
// Permission check helpers
// =============================================================================
export const useCanView = (feature: keyof UIPermissions): boolean => {
  const permissions = usePermissions();
  const featurePerms = permissions[feature];
  return 'view' in featurePerms ? featurePerms.view : false;
};

export const useCanCreate = (feature: keyof UIPermissions): boolean => {
  const permissions = usePermissions();
  const featurePerms = permissions[feature];
  return 'create' in featurePerms ? (featurePerms as { create: boolean }).create : false;
};

export const useCanEdit = (feature: keyof UIPermissions): boolean => {
  const permissions = usePermissions();
  const featurePerms = permissions[feature];
  return 'edit' in featurePerms ? (featurePerms as { edit: boolean }).edit : false;
};

export const useCanDelete = (feature: keyof UIPermissions): boolean => {
  const permissions = usePermissions();
  const featurePerms = permissions[feature];
  return 'delete' in featurePerms ? (featurePerms as { delete: boolean }).delete : false;
};

// =============================================================================
// Auth Provider
// =============================================================================
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<UIPermissions>(DEFAULT_PERMISSIONS);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    const storedPermissions = localStorage.getItem('permissions');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      
      // Restore permissions if available, otherwise use defaults
      if (storedPermissions) {
        try {
          setPermissions(JSON.parse(storedPermissions));
        } catch {
          setPermissions(DEFAULT_PERMISSIONS);
        }
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response = await authApi.login(username, password);
      
      // Store in state
      setToken(response.access_token);
      setUser(response.user);
      setPermissions(response.permissions);
      
      // Store in localStorage
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      localStorage.setItem('permissions', JSON.stringify(response.permissions));
    } catch (error) {
      throw error;
    }
  };

  const logout = (): void => {
    setToken(null);
    setUser(null);
    setPermissions(DEFAULT_PERMISSIONS);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('permissions');
  };

  const value: AuthContextType = {
    user,
    token,
    permissions,
    isLoading,
    isAuthenticated: !!token && !!user,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
