<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface Article {
		id: string;
		title: string;
		slug: string;
		language_id: number | null;
		tags: string[];
		published_at: string | null;
	}

	const LANG_BY_ID: Record<number, string> = { 1: '英文', 2: '日文', 3: '台語' };

	let articles: Article[] = [];
	let loading = true;
	let error = '';

	function fmtDate(iso: string | null): string {
		return iso ? iso.slice(0, 10) : '';
	}

	onMount(async () => {
		try {
			articles = await api.get<Article[]>('/blog');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>部落格 — Heniiii</title>
</svelte:head>

<section class="blog">
	<h1>部落格</h1>
	<p class="sub">語言學習資源與心得分享。</p>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if articles.length === 0}
		<p class="muted">目前還沒有文章。</p>
	{:else}
		<ul class="list">
			{#each articles as article (article.id)}
				<li>
					<a href={`/blog/${article.slug}`}>
						<div class="meta">
							{#if article.language_id}<span class="lang">{LANG_BY_ID[article.language_id] ?? ''}</span>{/if}
							<span class="date">{fmtDate(article.published_at)}</span>
						</div>
						<h2>{article.title}</h2>
						{#if article.tags.length}
							<div class="tags">
								{#each article.tags as tag}<span class="tag">#{tag}</span>{/each}
							</div>
						{/if}
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</section>

<style>
	.blog {
		max-width: 720px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2.4rem;
		font-weight: 800;
		color: #111;
	}

	.sub {
		color: #6b7280;
		margin-bottom: 2.5rem;
	}

	.list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.list a {
		display: block;
		text-decoration: none;
		color: #111;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid #e5e7eb;
	}

	.meta {
		display: flex;
		gap: 0.8rem;
		align-items: center;
		font-size: 0.8rem;
		color: #9ca3af;
		margin-bottom: 0.4rem;
	}

	.lang {
		background: #f3f4f6;
		padding: 0.1rem 0.5rem;
		border-radius: 999px;
	}

	.list h2 {
		font-size: 1.4rem;
		font-weight: 700;
	}

	.list a:hover h2 {
		text-decoration: underline;
	}

	.tags {
		margin-top: 0.5rem;
		display: flex;
		gap: 0.5rem;
	}

	.tag {
		font-size: 0.8rem;
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
