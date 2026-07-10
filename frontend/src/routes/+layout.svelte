<script lang="ts">
	import { isLoggedIn, currentUser, authStore } from '$lib/stores/auth';
</script>

<div class="app">
	<nav class="navbar">
		<a href="/" class="logo">Heniiii</a>

		<div class="nav-links">
			<a href="/learn/en">英文</a>
			<a href="/learn/ja">日文</a>
			<a href="/learn/tailo">台語</a>
			<a href="/daily">每日挑戰</a>
			<a href="/flashcards">單字卡</a>
			<a href="/leaderboard">排行榜</a>
			<a href="/blog">部落格</a>
			<a href="/search">搜尋</a>
			{#if $currentUser?.role === 'admin' || $currentUser?.role === 'editor'}
				<a href="/admin/lessons" class="admin-link">後台</a>
			{/if}
		</div>

		<div class="nav-auth">
			{#if $isLoggedIn}
				<a href="/profile">{$currentUser?.display_name}</a>
				<button on:click={() => authStore.logout()}>登出</button>
			{:else}
				<a href="/login">登入</a>
				<a href="/register" class="btn-register">註冊</a>
			{/if}
		</div>
	</nav>

	<main>
		<slot />
	</main>
</div>

<style>
	.app {
		min-height: 100vh;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
	}

	.navbar {
		display: flex;
		align-items: center;
		padding: 0 2rem;
		height: 64px;
		border-bottom: 1px solid #e5e7eb;
		background: white;
	}

	.logo {
		font-size: 1.5rem;
		font-weight: 700;
		color: #111;
		text-decoration: none;
		margin-right: 2rem;
	}

	.nav-links {
		display: flex;
		gap: 1.5rem;
		flex: 1;
		flex-wrap: wrap;
	}

	.nav-links a,
	.nav-auth a {
		text-decoration: none;
		color: #374151;
		font-size: 0.9rem;
	}

	.nav-links a:hover,
	.nav-auth a:hover {
		color: #111;
	}

	.nav-auth {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.btn-register {
		background: #111;
		color: white !important;
		padding: 0.5rem 1rem;
		border-radius: 6px;
	}

	.admin-link {
		font-weight: 600;
		color: #111 !important;
	}

	button {
		background: none;
		border: 1px solid #d1d5db;
		padding: 0.4rem 0.8rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.9rem;
	}

	main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}
</style>
