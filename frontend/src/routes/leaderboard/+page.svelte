<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import { currentUser } from '$lib/stores/auth';

	interface Entry {
		rank: number;
		user_id: string;
		display_name: string;
		score: number;
	}
	interface LeaderboardResponse {
		scope: string;
		lang: string | null;
		entries: Entry[];
	}

	const TABS = [
		{ key: 'total', scope: 'total', lang: null as string | null, label: '總排行' },
		{ key: 'en', scope: 'language', lang: 'en', label: '英文' },
		{ key: 'ja', scope: 'language', lang: 'ja', label: '日文' },
		{ key: 'tailo', scope: 'language', lang: 'tailo', label: '台語' },
		{ key: 'daily', scope: 'daily', lang: null, label: '每日挑戰' }
	];

	let activeKey = 'total';
	let entries: Entry[] = [];
	let loading = true;
	let error = '';

	const MEDAL = ['🥇', '🥈', '🥉'];

	async function load(key: string) {
		activeKey = key;
		loading = true;
		error = '';
		const tab = TABS.find((t) => t.key === key)!;
		try {
			const params = new URLSearchParams({ scope: tab.scope });
			if (tab.lang) params.set('lang', tab.lang);
			const data = await api.get<LeaderboardResponse>(`/leaderboard?${params.toString()}`);
			entries = data.entries;
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	onMount(() => load('total'));
</script>

<svelte:head>
	<title>排行榜 — Heniiii</title>
</svelte:head>

<section class="leaderboard">
	<h1>排行榜</h1>

	<div class="tabs">
		{#each TABS as tab (tab.key)}
			<button class="tab" class:active={activeKey === tab.key} on:click={() => load(tab.key)}>
				{tab.label}
			</button>
		{/each}
	</div>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if entries.length === 0}
		<p class="muted">目前還沒有排名資料。</p>
	{:else}
		<ol class="ranks">
			{#each entries as entry (entry.user_id)}
				<li class="rank" class:me={$currentUser?.id === entry.user_id} class:top={entry.rank <= 3}>
					<span class="pos">{MEDAL[entry.rank - 1] ?? entry.rank}</span>
					<span class="name">
						{entry.display_name}
						{#if $currentUser?.id === entry.user_id}<span class="you">你</span>{/if}
					</span>
					<span class="score">{entry.score}</span>
				</li>
			{/each}
		</ol>
	{/if}
</section>

<style>
	.leaderboard {
		max-width: 560px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2.4rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
	}

	.tabs {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.tab {
		border: 1px solid #d1d5db;
		background: white;
		padding: 0.45rem 1.1rem;
		border-radius: 999px;
		cursor: pointer;
		font-size: 0.9rem;
		color: #6b7280;
	}

	.tab.active {
		background: #111;
		color: white;
		border-color: #111;
	}

	.ranks {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.rank {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.9rem 1.2rem;
		border: 1px solid #e5e7eb;
		border-radius: 10px;
	}

	.rank.top {
		background: #fafafa;
	}

	.rank.me {
		border-color: #111;
		background: #f5f5f5;
	}

	.pos {
		width: 2rem;
		text-align: center;
		font-size: 1.2rem;
		font-weight: 700;
		color: #6b7280;
	}

	.name {
		flex: 1;
		font-weight: 600;
		color: #111;
	}

	.you {
		font-size: 0.7rem;
		background: #111;
		color: white;
		padding: 0.1rem 0.4rem;
		border-radius: 999px;
		margin-left: 0.4rem;
		vertical-align: middle;
	}

	.score {
		font-variant-numeric: tabular-nums;
		font-weight: 700;
		color: #111;
	}

	.muted {
		color: #9ca3af;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
	}
</style>
