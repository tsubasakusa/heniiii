<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { authStore, type AuthUser } from '$lib/stores/auth';

	let email = '';
	let password = '';
	let displayName = '';
	let error = '';
	let loading = false;

	async function handleRegister() {
		error = '';
		loading = true;
		try {
			const data = await api.post<{ access_token: string; refresh_token: string }>(
				'/auth/register',
				{ email, password, display_name: displayName }
			);
			authStore.setTokens(data.access_token, data.refresh_token);

			const user = await api.get<AuthUser>('/auth/me');
			authStore.setUser(user);

			goto('/');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '註冊失敗';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>註冊 — Heniiii</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-card">
		<h1>建立帳號</h1>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		<form on:submit|preventDefault={handleRegister}>
			<label>
				顯示名稱
				<input type="text" bind:value={displayName} required />
			</label>

			<label>
				Email
				<input type="email" bind:value={email} required />
			</label>

			<label>
				密碼
				<input type="password" bind:value={password} required minlength="8" />
			</label>

			<button type="submit" class="btn-primary" disabled={loading}>
				{loading ? '建立中...' : '建立帳號'}
			</button>
		</form>

		<p class="switch">已有帳號？<a href="/login">登入</a></p>
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
