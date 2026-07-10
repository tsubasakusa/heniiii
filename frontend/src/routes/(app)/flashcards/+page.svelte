<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface DeckSummary {
		id: string;
		title: string;
		language_id: number;
		card_count: number;
		due_count: number;
	}

	const LANG_BY_ID: Record<number, string> = { 1: '英文', 2: '日文', 3: '台語' };

	let decks: DeckSummary[] = [];
	let loading = true;
	let error = '';

	async function load() {
		loading = true;
		error = '';
		try {
			decks = await api.get<DeckSummary[]>('/flashcards');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	onMount(load);
</script>

<svelte:head>
	<title>單字卡 — Heniiii</title>
</svelte:head>

<section class="decks">
	<header class="head">
		<h1>我的單字卡</h1>
		<a href="/flashcards/new" class="btn-primary">+ 建立卡組</a>
	</header>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if decks.length === 0}
		<div class="empty">
			<p>還沒有任何卡組。</p>
			<a href="/flashcards/new" class="btn-primary">建立第一個卡組</a>
		</div>
	{:else}
		<ul class="grid">
			{#each decks as deck (deck.id)}
				<li class="card">
					<a href={`/flashcards/${deck.id}`} class="card-body">
						<span class="lang">{LANG_BY_ID[deck.language_id] ?? ''}</span>
						<h2>{deck.title}</h2>
						<p class="meta">{deck.card_count} 張卡片</p>
					</a>
					{#if deck.due_count > 0}
						<a href={`/flashcards/${deck.id}/practice`} class="due-btn">複習 {deck.due_count} 張 →</a>
					{:else}
						<span class="done-tag">今日已完成 ✓</span>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</section>

<style>
	.decks {
		max-width: 820px;
		margin: 0 auto;
	}

	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 2rem;
	}

	.head h1 {
		font-size: 2.2rem;
		font-weight: 800;
		color: #111;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.6rem 1.2rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
		white-space: nowrap;
	}

	.grid {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 1rem;
	}

	.card {
		border: 1px solid #e5e7eb;
		border-radius: 14px;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.card-body {
		padding: 1.3rem;
		text-decoration: none;
		color: #111;
		flex: 1;
	}

	.card-body:hover h2 {
		text-decoration: underline;
	}

	.lang {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	.card h2 {
		font-size: 1.3rem;
		font-weight: 700;
		margin: 0.3rem 0;
	}

	.meta {
		color: #6b7280;
		font-size: 0.9rem;
	}

	.due-btn {
		display: block;
		padding: 0.7rem 1.3rem;
		background: #111;
		color: white;
		text-decoration: none;
		font-size: 0.9rem;
		font-weight: 600;
	}

	.done-tag {
		display: block;
		padding: 0.7rem 1.3rem;
		background: #f3f4f6;
		color: #16a34a;
		font-size: 0.9rem;
	}

	.empty {
		text-align: center;
		padding: 4rem 1rem;
		color: #6b7280;
	}

	.empty p {
		margin-bottom: 1.5rem;
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
