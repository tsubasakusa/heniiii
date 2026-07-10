<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import { isLoggedIn } from '$lib/stores/auth';

	interface ContentBlock {
		type: string;
		value?: string;
		words?: string[];
		url?: string;
		[key: string]: unknown;
	}

	interface LessonDetail {
		id: string;
		title: string;
		language_id: number;
		difficulty_id: number;
		status: string;
		content: ContentBlock[];
	}

	let lang = '';
	let lessonId = '';
	let lesson: LessonDetail | null = null;
	let loading = true;
	let error = '';

	let completing = false;
	let completed = false;
	let completeError = '';

	async function load() {
		loading = true;
		error = '';
		try {
			lesson = await api.get<LessonDetail>(`/learn/lessons/${lessonId}`);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	async function complete() {
		if (!lesson) return;
		completing = true;
		completeError = '';
		try {
			// A simple full-completion score; richer scoring comes with exercises later.
			await api.post(`/learn/lessons/${lesson.id}/complete`, { score: 100 });
			completed = true;
		} catch (err) {
			completeError = (err as { detail?: string })?.detail || '無法記錄進度';
		} finally {
			completing = false;
		}
	}

	$: lang = $page.params.lang ?? '';
	$: lessonId = $page.params.id ?? '';

	onMount(() => {
		if ($isLoggedIn) load();
		else loading = false;
	});
</script>

<svelte:head>
	<title>{lesson?.title ?? '課程'} — Heniiii</title>
</svelte:head>

<article class="lesson">
	<a class="back" href={`/learn/${lang}`}>← 返回{lang === 'en' ? '英文' : lang === 'ja' ? '日文' : lang === 'tailo' ? '台語' : ''}課程</a>

	{#if !$isLoggedIn}
		<div class="gate">
			<h2>請先登入</h2>
			<p>登入後即可閱讀課程內容並記錄學習進度。</p>
			<a class="btn-primary" href="/login">前往登入</a>
		</div>
	{:else if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if lesson}
		<h1>{lesson.title}</h1>

		<div class="content">
			{#each lesson.content as block, i (i)}
				{#if block.type === 'text'}
					<p class="text">{block.value}</p>
				{:else if block.type === 'vocab_list'}
					<div class="vocab">
						<h3>單字</h3>
						<ul>
							{#each block.words ?? [] as word}
								<li>{word}</li>
							{/each}
						</ul>
					</div>
				{:else if block.type === 'audio' && block.url}
					<audio controls src={block.url}></audio>
				{:else}
					<pre class="raw">{JSON.stringify(block, null, 2)}</pre>
				{/if}
			{/each}

			{#if lesson.content.length === 0}
				<p class="muted">這堂課還沒有內容。</p>
			{/if}
		</div>

		<div class="actions">
			{#if completed}
				<p class="done">✓ 已完成，進度已記錄</p>
			{:else}
				<button class="btn-primary" on:click={complete} disabled={completing}>
					{completing ? '記錄中…' : '完成課程'}
				</button>
			{/if}
			{#if completeError}
				<p class="error">{completeError}</p>
			{/if}
		</div>
	{/if}
</article>

<style>
	.lesson {
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

	h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
	}

	.content {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}

	.text {
		font-size: 1.05rem;
		line-height: 1.8;
		color: #1f2937;
	}

	.vocab {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 10px;
		padding: 1rem 1.2rem;
	}

	.vocab h3 {
		font-size: 1rem;
		margin-bottom: 0.6rem;
		color: #111;
	}

	.vocab ul {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.vocab li {
		background: white;
		border: 1px solid #d1d5db;
		border-radius: 999px;
		padding: 0.3rem 0.9rem;
		font-size: 0.9rem;
	}

	.raw {
		background: #f3f4f6;
		padding: 0.8rem;
		border-radius: 8px;
		font-size: 0.8rem;
		overflow-x: auto;
	}

	.actions {
		margin-top: 2.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e5e7eb;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.8rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		display: inline-block;
	}

	.btn-primary:disabled {
		opacity: 0.5;
	}

	.gate {
		text-align: center;
		padding: 4rem 1rem;
	}

	.gate h2 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.gate p {
		color: #6b7280;
		margin-bottom: 1.5rem;
	}

	.done {
		color: #059669;
		font-weight: 600;
	}

	.muted {
		color: #9ca3af;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		margin-top: 1rem;
	}
</style>
