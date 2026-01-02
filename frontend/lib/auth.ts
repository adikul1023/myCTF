/**
 * Authentication utilities for Investigation Portal
 * Client-side auth state management
 */

import { api, setToken, clearToken, getToken } from './api';

export interface User {
  id: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

/**
 * Get current authenticated user
 * Returns null if not authenticated
 */
export async function getCurrentUser(): Promise<User | null> {
  const response = await api.getCurrentUser();
  if (response.status === 200 && response.data) {
    return response.data as User;
  }
  return null;
}

/**
 * Login with email and password
 */
export async function login(
  email: string,
  password: string
): Promise<{ success: boolean; error?: string }> {
  const response = await api.login(email, password);
  if (response.status === 200 && (response.data as any)?.access_token) {
    setToken((response.data as any).access_token);
    return { success: true };
  }
  return { success: false, error: response.error || 'Login failed' };
}

/**
 * Register new user (requires invite code)
 */
export async function register(
  email: string,
  username: string,
  password: string,
  inviteCode: string
): Promise<{ success: boolean; error?: string }> {
  const response = await api.register(email, username, password, inviteCode);
  if (response.status === 201) {
    return { success: true };
  }
  return { success: false, error: response.error || 'Registration failed' };
}

/**
 * Logout current user
 */
export async function logout(): Promise<void> {
  clearToken();
  window.location.href = '/login';
}

/**
 * Check if user is authenticated (has token)
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}
