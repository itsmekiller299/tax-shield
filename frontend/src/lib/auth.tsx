'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/types';
import { api } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; name: string }) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = api.getToken();
      if (token) {
        try {
          const userData = await api.getCurrentUser();
          setUser(userData);
        } catch {
          api.clearToken();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const data = await api.login(email, password);
      api.setToken(data.access_token);
    } catch (error: any) {
      // Demo Mode (as promised on the login page): unknown email → auto-register
      if (error?.response?.status !== 401) throw error;
      const name = email.split('@')[0].replace(/[._-]+/g, ' ').trim() || 'Demo User';
      const result = await api.register({ email, password, name });
      api.setToken(result.access_token);
    }
    const userData = await api.getCurrentUser();
    setUser(userData);
  };

  const register = async (data: { email: string; password: string; name: string }) => {
    const result = await api.register(data);
    api.setToken(result.access_token);
    const userData = await api.getCurrentUser();
    setUser(userData);
  };

  const logout = () => {
    api.clearToken();
    setUser(null);
  };

  const refreshUser = async () => {
    if (api.getToken()) {
      try {
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch {
        api.clearToken();
        setUser(null);
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}