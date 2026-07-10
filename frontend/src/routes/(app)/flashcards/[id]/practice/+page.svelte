<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface Card {
		id: string;
		front_text: string;
		back_text: string;
		pronunciation: string | null;
	}

	const RATINGS = [
		{ q: 1, label: '忘記了', klass: 'again' },
		{ q: 3, label: '有點難', klass: 'hard' },
		{ q: 4, label: '記得', klass: 'good' },
		{ q: 5, label: '很簡單', klass: 'easy' }
	];

	let deckId = '';
	let queue: Card[] = [];
	let index = 0;
	let flipped = false;
	let loading = true;
	let error = '';
	let submitting = false;
	let reviewed = 0;

	$: deckId = $page.params.id ?? '';
	$: current = queue[index] ?? null;
	$: total = queue.length;

	async function load() {
		loading = true;
		error = '';
		try {
			queue = await api.get<Card[]>(`/flashcards/${deckId}/due`);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	async function rate(quality: number) {
		if (!current || submitting) return;
		submitting = true;
		try {
			await api.post(`/flashcards/cards/${current.id}/review`, { quality });
			reviewed += 1;
			flipped = false;
			index += 1;
		} catch (err) {
			error = (err as { detail?: string })?.detail || '提交失敗';
		} finally {
			submitting = false;
		}
	}

	onMount(load);
</script>

<svelte:head>
	<title>複習 — Heniiii</title>
</svelte:head>

<section class="practice">
	<a class="back" href={`/flashcards/${deckId}`}>← 返回卡組</a>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if total === 0}
		<div class="done">
			<h2>目前沒有到期的卡片 🎉</h2>
			<p>晚點再回來複習吧。</p>
			<a href={`/flashcards/${deckId}`} class="btn-primary">返回卡組</a>
		</div>
	{:else if !current}
		<div class="done">
			<h2>複習完成！🎉</h2>
			<p>這次複習了 {reviewed} 張卡片。</p>
			<a href="/flashcards" class="btn-primary">回到我的單字卡</a>
		</div>
	{:else}
		<div class="progress">{index + 1} / {total}</div>

		<div class="flashcard" class:flipped on:click={() => (flipped = true)} role="button" tabindex="0"
			on:keydown={(e) => e.key === 'Enter' && (flipped = true)}>
			{#if !flipped}
				<div class="face front">
					<span class="text">{current.front_text}</span>
					<span class="hint">點擊顯示答案</span>
				</div>
			{:else}
				<div class="face back">
					<span class="text">{current.back_text}</span>
					{#if current.pronunciation}<span class="pron">{current.pronunciation}</span>{/if}
				</div>
			{/if}
		</div>

		{#if flipped}
			<div class="ratings">
				{#each RATINGS as r (r.q)}
					<button class={`rate ${r.klass}`} on:click={() => rate(r.q)} disabled={submitting}>
						{r.label}
					</button>
				{/each}
			</div>
			<p class="hint-below">依熟悉度自評，系統會安排下次複習時間</p>
		{:else}
			<button class="show-btn" on:click={() => (flipped = true)}>顯示答案</button>
		{/if}
	{/if}
</section>

<style>
	.practice {
		max-width: 560px;
		margin: 0 auto;
		text-align: center;
	}

	.back {
		display: block;
		text-align: left;
		margin-bottom: 1.5rem;
		color: #6b7280;
		text-decoration: none;
		font-size: 0.9rem;
	}
	.back:hover {
		color: #111;
	}

	.progress {
		color: #9ca3af;
		font-variant-numeric: tabular-nums;
		margin-bottom: 1rem;
	}

	.flashcard {
		border: 1px solid #e5e7eb;
		border-radius: 16px;
		min-height: 220px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		margin-bottom: 1.5rem;
		transition: border-color 0.15s;
	}
	.flashcard:hover {
		border-color: #111;
	}
	.flashcard.flipped {
		background: #f9fafb;
		cursor: default;
	}

	.face {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.6rem;
		padding: 2rem;
	}

	.text {
		font-size: 2rem;
		font-weight: 700;
		color: #111;
	}

	.pron {
		color: #6b7280;
	}

	.hint {
		font-size: 0.8rem;
		color: #9ca3af;
	}

	.show-btn {
		background: #111;
		color: white;
		padding: 0.8rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
	}

	.ratings {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.6rem;
	}

	.rate {
		padding: 0.8rem 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 8px;
		background: white;
		cursor: pointer;
		font-size: 0.95rem;
		font-weight: 600;
	}
	.rate:disabled {
		opacity: 0.5;
	}
	.rate.again {
		color: #dc2626;
		border-color: #fecaca;
	}
	.rate.hard {
		color: #d97706;
		border-color: #fed7aa;
	}
	.rate.good {
		color: #2563eb;
		border-color: #bfdbfe;
	}
	.rate.easy {
		color: #16a34a;
		border-color: #bbf7d0;
	}

	.hint-below {
		margin-top: 1rem;
		font-size: 0.8rem;
		color: #9ca3af;
	}

	.done {
		padding: 4rem 1rem;
	}
	.done h2 {
		font-size: 1.6rem;
		margin-bottom: 0.5rem;
	}
	.done p {
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
