<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import { renderMarkdown } from '$lib/markdown';

	interface Article {
		title: string;
		slug: string;
		content: string;
		cover_image_url: string | null;
		language_id: number | null;
		tags: string[];
		published_at: string | null;
	}

	const LANG_BY_ID: Record<number, string> = { 1: '英文', 2: '日文', 3: '台語' };

	let slug = '';
	let article: Article | null = null;
	let loading = true;
	let error = '';

	$: slug = $page.params.slug ?? '';
	$: rendered = article ? renderMarkdown(article.content) : '';

	onMount(async () => {
		try {
			article = await api.get<Article>(`/blog/${slug}`);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '找不到文章';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>{article?.title ?? '文章'} — Heniiii</title>
</svelte:head>

<article class="post">
	<a class="back" href="/blog">← 部落格</a>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if article}
		<div class="meta">
			{#if article.language_id}<span class="lang">{LANG_BY_ID[article.language_id] ?? ''}</span>{/if}
			{#if article.published_at}<span>{article.published_at.slice(0, 10)}</span>{/if}
		</div>
		<h1>{article.title}</h1>
		{#if article.cover_image_url}
			<img class="cover" src={article.cover_image_url} alt={article.title} />
		{/if}
		<!-- content is escaped inside renderMarkdown before formatting -->
		<div class="content">{@html rendered}</div>
		{#if article.tags.length}
			<div class="tags">
				{#each article.tags as tag}<span class="tag">#{tag}</span>{/each}
			</div>
		{/if}
	{/if}
</article>

<style>
	.post {
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

	.meta {
		display: flex;
		gap: 0.8rem;
		align-items: center;
		font-size: 0.85rem;
		color: #9ca3af;
		margin-bottom: 0.5rem;
	}

	.lang {
		background: #f3f4f6;
		padding: 0.1rem 0.5rem;
		border-radius: 999px;
	}

	h1 {
		font-size: 2.2rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
	}

	.cover {
		width: 100%;
		border-radius: 12px;
		margin-bottom: 1.5rem;
	}

	.content {
		line-height: 1.8;
		color: #1f2937;
	}

	.content :global(h1),
	.content :global(h2),
	.content :global(h3) {
		color: #111;
		margin: 1.5rem 0 0.8rem;
	}

	.content :global(p) {
		margin: 1rem 0;
	}

	.content :global(ul),
	.content :global(ol) {
		margin: 1rem 0;
		padding-left: 1.5rem;
	}

	.content :global(li) {
		margin: 0.3rem 0;
	}

	.content :global(code) {
		background: #f3f4f6;
		padding: 0.1rem 0.3rem;
		border-radius: 4px;
		font-size: 0.9em;
	}

	.content :global(blockquote) {
		border-left: 3px solid #d1d5db;
		padding-left: 1rem;
		color: #6b7280;
		margin: 1rem 0;
	}

	.content :global(a) {
		color: #2563eb;
	}

	.tags {
		margin-top: 2rem;
		display: flex;
		gap: 0.6rem;
	}

	.tag {
		font-size: 0.85rem;
		color: #6b7280;
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
