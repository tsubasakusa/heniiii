<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface PuzzleSummary {
		id: string;
		publish_date: string;
		language_id: number;
	}

	const LANG_BY_ID: Record<number, string> = { 1: '英文', 2: '日文', 3: '台語' };

	let puzzles: PuzzleSummary[] = [];
	let loading = true;
	let error = '';

	onMount(async () => {
		try {
			puzzles = await api.get<PuzzleSummary[]>('/daily/crossword/archive');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>歷史題目 — Heniiii</title>
</svelte:head>

<section class="archive">
	<a class="back" href="/daily">← 每日挑戰</a>
	<h1>歷史題目</h1>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if puzzles.length === 0}
		<p class="muted">目前沒有歷史題目。</p>
	{:else}
		<ul class="list">
			{#each puzzles as p (p.id)}
				<li>
					<a href={`/daily/crossword?date=${p.publish_date}`}>
						<span class="date">{p.publish_date}</span>
						<span class="lang">{LANG_BY_ID[p.language_id] ?? ''}填字</span>
						<span class="arrow">→</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</section>

<style>
	.archive {
		max-width: 560px;
		margin: 0 auto;
	}

	.back {
		display: inline-block;
		margin-bottom: 1.5rem;
		color: #6b7280;
		text-decoration: none;
		font-size: 0.9rem;
	}
	.back:hover {
		color: #111;
	}

	h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
	}

	.list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.list a {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem 1.2rem;
		border: 1px solid #e5e7eb;
		border-radius: 10px;
		text-decoration: none;
		color: #111;
	}
	.list a:hover {
		border-color: #111;
	}

	.date {
		font-weight: 600;
		font-variant-numeric: tabular-nums;
	}

	.lang {
		color: #6b7280;
		font-size: 0.9rem;
		flex: 1;
	}

	.arrow {
		color: #9ca3af;
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
