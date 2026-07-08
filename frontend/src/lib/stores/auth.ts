import { writable, derived } from 'svelte/store';

export interface AuthUser {
	id: string;
	email: string;
	display_name: string;
	avatar_url: string | null;
	role: string;
}

interface AuthState {
	accessToken: string | null;
	refreshToken: string | null;
	user: AuthUser | null;
}

const EMPTY_STATE: AuthState = {
	accessToken: null,
	refreshToken: null,
	user: null
};

function readStoredState(): AuthState {
	if (typeof localStorage === 'undefined') return EMPTY_STATE;
	try {
		const stored = JSON.parse(localStorage.getItem('auth') || 'null');
		return stored ?? EMPTY_STATE;
	} catch {
		return EMPTY_STATE;
	}
}

function persist(state: AuthState) {
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem('auth', JSON.stringify(state));
	}
}

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(readStoredState());

	return {
		subscribe,

		setTokens(accessToken: string, refreshToken: string) {
			update((state) => {
				const newState = { ...state, accessToken, refreshToken };
				persist(newState);
				return newState;
			});
		},

		setUser(user: AuthUser | null) {
			update((state) => {
				const newState = { ...state, user };
				persist(newState);
				return newState;
			});
		},

		logout() {
			set(EMPTY_STATE);
			persist(EMPTY_STATE);
		}
	};
}

export const authStore = createAuthStore();
export const isLoggedIn = derived(authStore, ($auth) => !!$auth.accessToken);
export const currentUser = derived(authStore, ($auth) => $auth.user);
