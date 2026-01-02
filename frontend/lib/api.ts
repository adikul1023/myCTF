/**
 * API Client for Investigation Portal
 * Handles all backend communication with JWT authentication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

const TOKEN_KEY = 'ctf_access_token';

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

// Token management
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const token = getToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
      });

      // Handle 401 Unauthorized - session expired
      if (response.status === 401) {
        clearToken();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return {
          status: 401,
          error: 'Session expired. Please log in again.',
        };
      }

      const data = await response.json();

      if (!response.ok) {
        return {
          status: response.status,
          error: data.detail || 'Request failed',
        };
      }

      return {
        status: response.status,
        data,
      };
    } catch (error) {
      return {
        status: 500,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Authentication
  async register(email: string, username: string, password: string, inviteCode: string) {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password, invite_code: inviteCode }),
    });
  }

  async login(email: string, password: string) {
    return this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async logout() {
    return this.request('/api/v1/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser() {
    return this.request('/api/v1/auth/me');
  }

  // Cases
  async getCases() {
    return this.request('/api/v1/cases');
  }

  async getCase(caseId: string) {
    return this.request(`/api/v1/cases/${caseId}`);
  }

  async getCaseArtifacts(caseId: string) {
    return this.request(`/api/v1/cases/${caseId}/artifacts`);
  }

  async downloadArtifact(caseId: string, artifactId: string) {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(
      `${this.baseUrl}/api/v1/cases/${caseId}/artifacts/${artifactId}/download`,
      { headers }
    );
    // Handle 401 - redirect to login
    if (response.status === 401) {
      clearToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return response;
  }

  // Submissions (replaces challenges)
  async submitAnswer(caseId: string, answer: string) {
    return this.request('/api/v1/submissions/submit', {
      method: 'POST',
      body: JSON.stringify({ case_id: caseId, answer }),
    });
  }

  async getSubmissions(caseId?: string) {
    const query = caseId ? `?case_id=${caseId}` : '';
    return this.request(`/api/v1/submissions/history${query}`);
  }

  async getCaseStatus(caseId: string) {
    return this.request(`/api/v1/submissions/case/${caseId}/my-status`);
  }

  async getChallenges(caseId: string) {
    return this.request(`/api/v1/cases/${caseId}/challenges`);
  }

  async submitChallengeAnswer(challengeId: string, answer: string) {
    return this.request(`/api/v1/challenges/${challengeId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  }

  // Admin
  async createCase(caseData: any) {
    return this.request('/api/v1/admin/cases', {
      method: 'POST',
      body: JSON.stringify(caseData),
    });
  }

  async uploadArtifact(caseId: string, file: File, metadata: any) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${this.baseUrl}/api/v1/admin/cases/${caseId}/artifacts`,
      {
        method: 'POST',
        body: formData,
        headers,
      }
    );

    const data = await response.json();
    return {
      status: response.status,
      data: response.ok ? data : undefined,
      error: response.ok ? undefined : data.detail || 'Upload failed',
    };
  }

  // Invite codes
  async generateInviteCode(maxUses: number = 1, expiresInDays?: number) {
    return this.request('/api/v1/admin/invite-codes', {
      method: 'POST',
      body: JSON.stringify({ max_uses: maxUses, expires_in_days: expiresInDays }),
    });
  }

  async listInviteCodes() {
    return this.request('/api/v1/admin/invite-codes');
  }
}

export const api = new ApiClient(API_URL);
