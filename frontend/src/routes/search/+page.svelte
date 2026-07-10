<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';

	interface SearchResult {
		type: string;
		id: string;
		title: string;
		subtitle: string;
		language_id: number | null;
		slug: string | null;
	}
	interface SearchResponse {
		query: string;
		total: number;
		results: SearchResult[];
	}

	const LANG_CODE: Record<number, string> = { 1: 'en', 2: 'ja', 3: 'tailo' };
	const TYPE_LABEL: Record<string, string> = {
		lesson: '課程',
		vocabulary: '單字',
		article: '文章'
	};
	const FILTERS = [
		{ key: '', label: '全部' },
		{ key: 'lesson', label: '課程' },
		{ key: 'vocabulary', label: '單字' },
		{ key: 'article', label: '文章' }
	];

	let query = '';
	let typeFilter = '';
	let results: SearchResult[] = [];
	let total = 0;
	let loading = false;
	let searched = false;
	let error = '';

	function linkFor(r: SearchResult): string {
		const lang = r.language_id ? LANG_CODE[r.language_id] : 'en';
		if (r.type === 'lesson') return `/learn/${lang}/lesson/${r.id}`;
		if (r.type === 'vocabulary') return `/learn/${lang}/vocabulary`;
		if (r.type === 'article') return `/blog/${r.slug}`;
		return '#';
	}

	async function runSearch() {
		if (!query.trim()) {
			results = [];
			total = 0;
			searched = false;
			return;
		}
		loading = true;
		error = '';
		searched = true;
		try {
			const params = new URLSearchParams({ q: query.trim() });
			if (typeFilter) params.set('type', typeFilter);
			const data = await api.get<SearchResponse>(`/search?${params.toString()}`);
			results = data.results;
			total = data.total;
		} catch (err) {
			error = (err as { detail?: string })?.detail || '搜尋失敗';
		} finally {
			loading = false;
		}
	}

	function onSubmit() {
		const params = new URLSearchParams({ q: query.trim() });
		goto(`/search?${params.toString()}`, { replaceState: true, keepFocus: true });
		runSearch();
	}

	function setFilter(key: string) {
		typeFilter = key;
		runSearch();
	}

	onMount(() => {
		query = $page.url.searchParams.get('q') ?? '';
		if (query) runSearch();
	});
</script>

<svelte:head>
	<title>搜尋 — Heniiii</title>
</svelte:head>

<section class="search">
	<h1>搜尋</h1>

	<form on:submit|preventDefault={onSubmit} class="search-box">
		<input type="search" bind:value={query} placeholder="搜尋課程、單字、文章…" />
		<button type="submit" class="btn-primary">搜尋</button>
	</form>

	<div class="filters">
		{#each FILTERS as f (f.key)}
			<button class="filter" class:active={typeFilter === f.key} on:click={() => setFilter(f.key)}>
				{f.label}
			</button>
		{/each}
	</div>

	{#if loading}
		<p class="muted">搜尋中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if searched && total === 0}
		<p class="muted">找不到「{query}」的結果。</p>
	{:else if searched}
		<p class="count">共 {total} 筆結果</p>
		<ul class="results">
			{#each results as r (r.type + r.id)}
				<li>
					<a href={linkFor(r)}>
						<span class="type-badge {r.type}">{TYPE_LABEL[r.type] ?? r.type}</span>
						<span class="text">
							<span class="title">{r.title}</span>
							<span class="subtitle">{r.subtitle}</span>
						</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</section>

<style>
	.search {
		max-width: 680px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2.2rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
	}

	.search-box {
		display: flex;
		gap: 0.6rem;
		margin-bottom: 1rem;
	}

	.search-box input {
		flex: 1;
		padding: 0.7rem 1rem;
		border: 1px solid #d1d5db;
		border-radius: 8px;
		font-size: 1rem;
		font-family: inherit;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.7rem 1.5rem;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
	}

	.filters {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 2rem;
	}

	.filter {
		border: 1px solid #d1d5db;
		background: white;
		padding: 0.4rem 1rem;
		border-radius: 999px;
		cursor: pointer;
		font-size: 0.9rem;
		color: #6b7280;
	}

	.filter.active {
		background: #111;
		color: white;
		border-color: #111;
	}

	.count {
		color: #9ca3af;
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.results {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.results a {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 10px;
		text-decoration: none;
		color: #111;
	}

	.results a:hover {
		border-color: #111;
	}

	.type-badge {
		font-size: 0.75rem;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		white-space: nowrap;
	}
	.type-badge.lesson {
		background: #dbeafe;
		color: #1e40af;
	}
	.type-badge.vocabulary {
		background: #dcfce7;
		color: #166534;
	}
	.type-badge.article {
		background: #fef3c7;
		color: #92400e;
	}

	.text {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		overflow: hidden;
	}

	.title {
		font-weight: 600;
	}

	.subtitle {
		font-size: 0.85rem;
		color: #6b7280;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
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
