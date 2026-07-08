<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { authStore, type AuthUser } from '$lib/stores/auth';

	let email = '';
	let password = '';
	let error = '';
	let loading = false;

	async function handleLogin() {
		error = '';
		loading = true;
		try {
			const data = await api.post<{ access_token: string; refresh_token: string }>(
				'/auth/login',
				{ email, password }
			);
			authStore.setTokens(data.access_token, data.refresh_token);

			const user = await api.get<AuthUser>('/auth/me');
			authStore.setUser(user);

			goto('/');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '登入失敗';
		} finally {
			loading = false;
		}
	}

	function oauthLogin(provider: string) {
		window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/oauth/${provider}`;
	}
</script>

<svelte:head>
	<title>登入 — Heniiii</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-card">
		<h1>登入</h1>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		<form on:submit|preventDefault={handleLogin}>
			<label>
				Email
				<input type="email" bind:value={email} required />
			</label>

			<label>
				密碼
				<input type="password" bind:value={password} required />
			</label>

			<button type="submit" class="btn-primary" disabled={loading}>
				{loading ? '登入中...' : '登入'}
			</button>
		</form>

		<div class="divider">或</div>

		<div class="oauth-buttons">
			<button on:click={() => oauthLogin('google')}>Google 登入</button>
			<button on:click={() => oauthLogin('line')}>LINE 登入</button>
			<button on:click={() => oauthLogin('github')}>GitHub 登入</button>
		</div>

		<p class="switch">還沒有帳號？<a href="/register">註冊</a></p>
	</div>
</div>

<style>
	.auth-page {
		display: flex;
		justify-content: center;
		padding: 4rem 1rem;
	}

	.auth-card {
		width: 100%;
		max-width: 400px;
	}

	h1 {
		font-size: 1.8rem;
		margin-bottom: 1.5rem;
	}

	label {
		display: block;
		margin-bottom: 1rem;
		font-size: 0.9rem;
		color: #374151;
	}

	input {
		display: block;
		width: 100%;
		padding: 0.6rem;
		margin-top: 0.3rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 1rem;
		box-sizing: border-box;
	}

	.btn-primary {
		width: 100%;
		background: #111;
		color: white;
		padding: 0.7rem;
		border: none;
		border-radius: 6px;
		font-size: 1rem;
		cursor: pointer;
		margin-top: 0.5rem;
	}

	.btn-primary:disabled {
		opacity: 0.5;
	}

	.divider {
		text-align: center;
		color: #9ca3af;
		margin: 1.5rem 0;
		position: relative;
	}

	.oauth-buttons {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.oauth-buttons button {
		padding: 0.6rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		background: white;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		margin-bottom: 1rem;
	}

	.switch {
		text-align: center;
		margin-top: 1.5rem;
		color: #6b7280;
	}

	.switch a {
		color: #111;
		font-weight: 600;
	}
</style>
