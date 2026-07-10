<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface Level {
		id: number;
		slug: string;
		label_zh: string;
	}
	interface Vocab {
		id: string;
		difficulty_id: number;
		word: string;
		pronunciation: string;
		meaning_zh: string;
		example_sentence: string | null;
		audio_url: string | null;
	}

	const LANG_NAMES: Record<string, string> = { en: '英文', ja: '日文', tailo: '台語' };

	let lang = '';
	let langName = '';
	let levels: Level[] = [];
	let vocab: Vocab[] = [];
	let selectedLevel = '';
	let loading = true;
	let error = '';

	$: filtered = selectedLevel
		? vocab.filter((v) => v.difficulty_id === Number(selectedLevel))
		: vocab;

	function levelLabel(id: number): string {
		return levels.find((l) => l.id === id)?.label_zh ?? '';
	}

	async function load(code: string) {
		loading = true;
		error = '';
		try {
			[levels, vocab] = await Promise.all([
				api.get<Level[]>(`/learn/${code}/levels`),
				api.get<Vocab[]>(`/learn/${code}/vocabulary`)
			]);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	$: lang = $page.params.lang ?? '';
	$: langName = LANG_NAMES[lang] ?? lang;

	onMount(() => load(lang));

	let lastLoaded = '';
	$: if (lang && lang !== lastLoaded) {
		lastLoaded = lang;
		selectedLevel = '';
		load(lang);
	}
</script>

<svelte:head>
	<title>{langName}單字表 — Heniiii</title>
</svelte:head>

<section class="vocab">
	<header class="head">
		<div>
			<a class="back" href={`/learn/${lang}`}>← {langName}課程</a>
			<h1>{langName}單字表</h1>
		</div>
		{#if levels.length > 0}
			<label class="filter">
				難度
				<select bind:value={selectedLevel}>
					<option value="">全部</option>
					{#each levels as level (level.id)}
						<option value={String(level.id)}>{level.label_zh}</option>
					{/each}
				</select>
			</label>
		{/if}
	</header>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if filtered.length === 0}
		<p class="muted">目前尚無單字。</p>
	{:else}
		<ul class="cards">
			{#each filtered as v (v.id)}
				<li class="card">
					<div class="card-top">
						<span class="word">{v.word}</span>
						<span class="level">{levelLabel(v.difficulty_id)}</span>
					</div>
					<div class="pron">{v.pronunciation}</div>
					<div class="meaning">{v.meaning_zh}</div>
					{#if v.example_sentence}
						<div class="example">{v.example_sentence}</div>
					{/if}
					{#if v.audio_url}
						<audio controls src={v.audio_url}></audio>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</section>

<style>
	.vocab {
		max-width: 860px;
		margin: 0 auto;
	}

	.head {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		margin-bottom: 2rem;
	}

	.back {
		display: inline-block;
		color: #6b7280;
		text-decoration: none;
		font-size: 0.9rem;
		margin-bottom: 0.4rem;
	}

	.back:hover {
		color: #111;
	}

	.head h1 {
		font-size: 2.2rem;
		font-weight: 800;
		color: #111;
	}

	.filter {
		font-size: 0.85rem;
		color: #6b7280;
	}

	.filter select {
		margin-left: 0.5rem;
		padding: 0.4rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
	}

	.cards {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 1rem;
	}

	.card {
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 1.1rem;
	}

	.card-top {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
	}

	.word {
		font-size: 1.3rem;
		font-weight: 700;
		color: #111;
	}

	.level {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	.pron {
		color: #6b7280;
		font-size: 0.9rem;
		margin-top: 0.2rem;
	}

	.meaning {
		margin-top: 0.6rem;
		font-size: 1.05rem;
		color: #1f2937;
	}

	.example {
		margin-top: 0.5rem;
		font-size: 0.9rem;
		color: #6b7280;
		font-style: italic;
	}

	audio {
		margin-top: 0.6rem;
		width: 100%;
		height: 32px;
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
