<script lang="ts">
	import { currentUser, isLoggedIn } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';

	onMount(() => {
		if (!$isLoggedIn) {
			goto('/login');
			return;
		}
		if ($currentUser?.role !== 'admin' && $currentUser?.role !== 'editor') {
			goto('/');
		}
	});

	$: path = $page.url.pathname;
</script>

{#if $isLoggedIn && ($currentUser?.role === 'admin' || $currentUser?.role === 'editor')}
	<div class="admin-shell">
		<nav class="admin-nav">
			<span class="admin-title">後台管理</span>
			<a href="/admin/lessons" class:active={path.startsWith('/admin/lessons')}>課程管理</a>
			<a href="/admin/vocabulary" class:active={path.startsWith('/admin/vocabulary')}>單字管理</a>
			<a href="/admin/articles" class:active={path.startsWith('/admin/articles')}>文章管理</a>
		</nav>
		<slot />
	</div>
{/if}

<style>
	.admin-nav {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		max-width: 860px;
		margin: 0 auto 2rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #e5e7eb;
	}

	.admin-title {
		font-weight: 700;
		color: #111;
	}

	.admin-nav a {
		text-decoration: none;
		color: #6b7280;
		font-size: 0.95rem;
	}

	.admin-nav a.active {
		color: #111;
		font-weight: 600;
	}

	.admin-nav a:hover {
		color: #111;
	}
</style>
