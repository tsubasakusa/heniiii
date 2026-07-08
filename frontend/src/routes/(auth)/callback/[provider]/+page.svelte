<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { authStore, type AuthUser } from '$lib/stores/auth';

	let error = '';

	onMount(async () => {
		const provider = $page.params.provider;
		const code = $page.url.searchParams.get('code');

		if (!code) {
			error = '缺少授權碼';
			return;
		}

		try {
			const data = await api.post<{ access_token: string; refresh_token: string }>(
				`/auth/oauth/${provider}/callback?code=${code}`
			);
			authStore.setTokens(data.access_token, data.refresh_token);

			const user = await api.get<AuthUser>('/auth/me');
			authStore.setUser(user);

			goto('/');
		} catch (err) {
			error = (err as { detail?: string })?.detail || 'OAuth 登入失敗';
		}
	});
</script>

<div class="callback">
	{#if error}
		<p class="error">{error}</p>
		<a href="/login">返回登入</a>
	{:else}
		<p>登入中...</p>
	{/if}
</div>

<style>
	.callback {
		text-align: center;
		padding: 4rem;
	}

	.error {
		color: #dc2626;
		margin-bottom: 1rem;
	}
</style>
