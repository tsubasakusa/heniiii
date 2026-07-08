import { get } from 'svelte/store';
import { authStore } from '$lib/stores/auth';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiError {
	status: number;
	detail: string;
}

class ApiClient {
	private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
		const token = get(authStore).accessToken;

		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...((options.headers as Record<string, string>) || {})
		};

		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}

		const response = await fetch(`${API_BASE}${path}`, {
			...options,
			headers
		});

		if (response.status === 401 && token) {
			const refreshed = await this.tryRefresh();
			if (refreshed) {
				headers['Authorization'] = `Bearer ${get(authStore).accessToken}`;
				const retryResponse = await fetch(`${API_BASE}${path}`, { ...options, headers });
				if (!retryResponse.ok) throw await this.parseError(retryResponse);
				return retryResponse.json();
			}
			authStore.logout();
			window.location.href = '/login';
		}

		if (!response.ok) throw await this.parseError(response);
		return response.json();
	}

	private async tryRefresh(): Promise<boolean> {
		const refreshToken = get(authStore).refreshToken;
		if (!refreshToken) return false;

		try {
			const resp = await fetch(`${API_BASE}/auth/refresh?refresh_token=${refreshToken}`, {
				method: 'POST'
			});
			if (!resp.ok) return false;
			const data = await resp.json();
			authStore.setTokens(data.access_token, data.refresh_token);
			return true;
		} catch {
			return false;
		}
	}

	private async parseError(response: Response): Promise<ApiError> {
		const body = await response.json().catch(() => ({}));
		return { status: response.status, detail: body.detail || 'Unknown error' };
	}

	get<T>(path: string) {
		return this.request<T>(path);
	}

	post<T>(path: string, data?: unknown) {
		return this.request<T>(path, { method: 'POST', body: JSON.stringify(data) });
	}

	put<T>(path: string, data?: unknown) {
		return this.request<T>(path, { method: 'PUT', body: JSON.stringify(data) });
	}

	delete<T>(path: string) {
		return this.request<T>(path, { method: 'DELETE' });
	}
}

export const api = new ApiClient();
