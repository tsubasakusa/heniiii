<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';

	interface Card {
		id: string;
		front_text: string;
		back_text: string;
		pronunciation: string | null;
		next_review_at: string | null;
	}
	interface DeckDetail {
		id: string;
		title: string;
		language_id: number;
		cards: Card[];
	}

	let deckId = '';
	let deck: DeckDetail | null = null;
	let loading = true;
	let error = '';

	let front = '';
	let back = '';
	let pronunciation = '';
	let adding = false;

	$: deckId = $page.params.id ?? '';
	$: dueCount = deck
		? deck.cards.filter((c) => !c.next_review_at || new Date(c.next_review_at) <= new Date())
				.length
		: 0;

	async function load() {
		loading = true;
		error = '';
		try {
			deck = await api.get<DeckDetail>(`/flashcards/${deckId}`);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	async function addCard() {
		if (!front.trim() || !back.trim()) {
			error = '正面與背面都要填寫';
			return;
		}
		adding = true;
		error = '';
		try {
			await api.post(`/flashcards/${deckId}/cards`, {
				front_text: front,
				back_text: back,
				pronunciation: pronunciation || null
			});
			front = back = pronunciation = '';
			await load();
		} catch (err) {
			error = (err as { detail?: string })?.detail || '新增失敗';
		} finally {
			adding = false;
		}
	}

	async function removeCard(card: Card) {
		if (!confirm(`刪除「${card.front_text}」？`)) return;
		try {
			await api.delete(`/flashcards/cards/${card.id}`);
			if (deck) deck.cards = deck.cards.filter((c) => c.id !== card.id);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '刪除失敗';
		}
	}

	async function removeDeck() {
		if (!confirm('刪除整個卡組？此動作無法復原。')) return;
		try {
			await api.delete(`/flashcards/${deckId}`);
			goto('/flashcards');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '刪除失敗';
		}
	}

	onMount(load);
</script>

<svelte:head>
	<title>{deck?.title ?? '卡組'} — Heniiii</title>
</svelte:head>

<section class="deck">
	<a class="back" href="/flashcards">← 我的單字卡</a>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error && !deck}
		<p class="error">{error}</p>
	{:else if deck}
		<header class="head">
			<h1>{deck.title}</h1>
			{#if dueCount > 0}
				<a href={`/flashcards/${deckId}/practice`} class="btn-primary">開始複習（{dueCount} 張到期）</a>
			{:else if deck.cards.length > 0}
				<span class="done">今日已複習完成 ✓</span>
			{/if}
		</header>

		<div class="add-card">
			<h3>新增卡片</h3>
			<div class="add-fields">
				<input placeholder="正面（單字）" bind:value={front} />
				<input placeholder="背面（意思）" bind:value={back} />
				<input placeholder="發音（選填）" bind:value={pronunciation} />
				<button class="btn-primary" on:click={addCard} disabled={adding}>
					{adding ? '新增中…' : '新增'}
				</button>
			</div>
			{#if error}<p class="error">{error}</p>{/if}
		</div>

		{#if deck.cards.length === 0}
			<p class="muted">還沒有卡片，先新增幾張吧。</p>
		{:else}
			<ul class="cards">
				{#each deck.cards as card (card.id)}
					<li>
						<div class="card-text">
							<span class="front">{card.front_text}</span>
							<span class="sep">→</span>
							<span class="back">{card.back_text}</span>
							{#if card.pronunciation}<span class="pron">{card.pronunciation}</span>{/if}
						</div>
						<button class="link-danger" on:click={() => removeCard(card)}>刪除</button>
					</li>
				{/each}
			</ul>
		{/if}

		<button class="delete-deck" on:click={removeDeck}>刪除卡組</button>
	{/if}
</section>

<style>
	.deck {
		max-width: 680px;
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

	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.head h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.6rem 1.3rem;
		border: none;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
		font-size: 0.95rem;
		cursor: pointer;
		white-space: nowrap;
	}
	.btn-primary:disabled {
		opacity: 0.5;
	}

	.done {
		color: #16a34a;
		font-weight: 600;
	}

	.add-card {
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 1.2rem;
		margin-bottom: 2rem;
	}

	.add-card h3 {
		font-size: 1rem;
		margin-bottom: 0.8rem;
		color: #111;
	}

	.add-fields {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.add-fields input {
		flex: 1;
		min-width: 120px;
		padding: 0.55rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 0.95rem;
		font-family: inherit;
	}

	.cards {
		list-style: none;
		padding: 0;
		margin: 0 0 2rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.cards li {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.8rem 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
	}

	.card-text {
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.front {
		font-weight: 700;
		color: #111;
	}
	.sep {
		color: #9ca3af;
	}
	.back {
		color: #374151;
	}
	.pron {
		color: #9ca3af;
		font-size: 0.85rem;
	}

	.link-danger {
		background: none;
		border: none;
		color: #dc2626;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.delete-deck {
		background: none;
		border: 1px solid #e5e7eb;
		color: #6b7280;
		padding: 0.5rem 1rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.85rem;
	}
	.delete-deck:hover {
		border-color: #dc2626;
		color: #dc2626;
	}

	.muted {
		color: #9ca3af;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		margin-top: 0.8rem;
	}
</style>
