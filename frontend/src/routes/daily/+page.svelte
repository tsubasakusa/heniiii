<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface Puzzle {
		id: string;
		publish_date: string;
		language_id: number;
	}
	interface TodayResponse {
		date: string;
		puzzle: Puzzle | null;
	}

	const LANG_BY_ID: Record<number, string> = { 1: '英文', 2: '日文', 3: '台語' };

	let today = '';
	let puzzle: Puzzle | null = null;
	let loading = true;
	let error = '';

	onMount(async () => {
		try {
			const data = await api.get<TodayResponse>('/daily/today');
			today = data.date;
			puzzle = data.puzzle;
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>每日挑戰 — Heniiii</title>
</svelte:head>

<section class="daily">
	<h1>每日挑戰</h1>
	<p class="date">{today}</p>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if puzzle}
		<div class="card">
			<div class="card-top">
				<span class="tag">填字遊戲</span>
				<span class="lang">{LANG_BY_ID[puzzle.language_id] ?? ''}</span>
			</div>
			<h2>今日填字</h2>
			<p>解開字謎、越快完成分數越高。</p>
			<a class="btn-primary" href="/daily/crossword">開始挑戰</a>
		</div>
	{:else}
		<p class="muted">今日尚無題目，敬請期待。</p>
	{/if}

	<a class="archive-link" href="/daily/crossword/archive">歷史題目 →</a>
</section>

<style>
	.daily {
		max-width: 640px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2.4rem;
		font-weight: 800;
		color: #111;
	}

	.date {
		color: #9ca3af;
		margin-bottom: 2rem;
	}

	.card {
		border: 1px solid #e5e7eb;
		border-radius: 16px;
		padding: 2rem;
	}

	.card-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.tag {
		background: #111;
		color: white;
		font-size: 0.75rem;
		padding: 0.25rem 0.7rem;
		border-radius: 999px;
	}

	.lang {
		color: #6b7280;
		font-size: 0.9rem;
	}

	.card h2 {
		font-size: 1.5rem;
		color: #111;
		margin-bottom: 0.4rem;
	}

	.card p {
		color: #6b7280;
		margin-bottom: 1.5rem;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.8rem 2rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
		display: inline-block;
	}

	.archive-link {
		display: inline-block;
		margin-top: 2rem;
		color: #6b7280;
		text-decoration: none;
		font-size: 0.9rem;
	}

	.archive-link:hover {
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
