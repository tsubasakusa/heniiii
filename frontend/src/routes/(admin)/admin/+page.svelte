<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface LanguageStat {
		language_id: number;
		name_zh: string;
		learner_count: number;
	}
	interface RecentItem {
		id: string;
		title: string;
		published_at: string | null;
	}
	interface Stats {
		total_users: number;
		new_users_today: number;
		total_lessons: number;
		published_lessons: number;
		total_articles: number;
		published_articles: number;
		total_vocabulary: number;
		total_decks: number;
		crossword_submissions_today: number;
		language_distribution: LanguageStat[];
		recent_lessons: RecentItem[];
		recent_articles: RecentItem[];
	}

	let stats: Stats | null = null;
	let loading = true;
	let error = '';

	$: maxLearners = stats
		? Math.max(1, ...stats.language_distribution.map((l) => l.learner_count))
		: 1;

	onMount(async () => {
		try {
			stats = await api.get<Stats>('/admin/dashboard');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>儀表板 — Heniiii 後台</title>
</svelte:head>

<section class="dashboard">
	<h1>儀表板</h1>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if stats}
		<div class="cards">
			<div class="stat">
				<span class="num">{stats.total_users}</span>
				<span class="label">使用者總數</span>
				<span class="sub">今日新增 {stats.new_users_today}</span>
			</div>
			<div class="stat">
				<span class="num">{stats.published_lessons}</span>
				<span class="label">已發布課程</span>
				<span class="sub">共 {stats.total_lessons} 堂</span>
			</div>
			<div class="stat">
				<span class="num">{stats.total_vocabulary}</span>
				<span class="label">單字庫</span>
			</div>
			<div class="stat">
				<span class="num">{stats.published_articles}</span>
				<span class="label">已發布文章</span>
				<span class="sub">共 {stats.total_articles} 篇</span>
			</div>
			<div class="stat">
				<span class="num">{stats.total_decks}</span>
				<span class="label">單字卡組</span>
			</div>
			<div class="stat">
				<span class="num">{stats.crossword_submissions_today}</span>
				<span class="label">今日填字提交</span>
			</div>
		</div>

		<div class="panels">
			<div class="panel">
				<h2>各語言學習人數</h2>
				{#if stats.language_distribution.every((l) => l.learner_count === 0)}
					<p class="muted small">尚無學習紀錄。</p>
				{:else}
					<ul class="bars">
						{#each stats.language_distribution as lang (lang.language_id)}
							<li>
								<span class="bar-label">{lang.name_zh}</span>
								<div class="bar-track">
									<div class="bar-fill" style={`width:${(lang.learner_count / maxLearners) * 100}%`}></div>
								</div>
								<span class="bar-value">{lang.learner_count}</span>
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			<div class="panel">
				<h2>最近發布</h2>
				<h3>課程</h3>
				{#if stats.recent_lessons.length === 0}
					<p class="muted small">尚無課程</p>
				{:else}
					<ul class="recent">
						{#each stats.recent_lessons as l (l.id)}
							<li>{l.title}</li>
						{/each}
					</ul>
				{/if}
				<h3>文章</h3>
				{#if stats.recent_articles.length === 0}
					<p class="muted small">尚無文章</p>
				{:else}
					<ul class="recent">
						{#each stats.recent_articles as a (a.id)}
							<li>{a.title}</li>
						{/each}
					</ul>
				{/if}
			</div>
		</div>
	{/if}
</section>

<style>
	.dashboard {
		max-width: 860px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
	}

	.cards {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
		gap: 1rem;
		margin-bottom: 2.5rem;
	}

	.stat {
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 1.2rem;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.num {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
		line-height: 1;
	}

	.label {
		font-size: 0.9rem;
		color: #374151;
		margin-top: 0.3rem;
	}

	.sub {
		font-size: 0.8rem;
		color: #9ca3af;
	}

	.panels {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.panel {
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 1.3rem;
	}

	.panel h2 {
		font-size: 1.1rem;
		color: #111;
		margin-bottom: 1rem;
	}

	.panel h3 {
		font-size: 0.85rem;
		color: #6b7280;
		margin: 1rem 0 0.5rem;
	}

	.bars {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.7rem;
	}

	.bars li {
		display: flex;
		align-items: center;
		gap: 0.7rem;
	}

	.bar-label {
		width: 3rem;
		font-size: 0.9rem;
		color: #374151;
	}

	.bar-track {
		flex: 1;
		height: 10px;
		background: #f3f4f6;
		border-radius: 999px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		background: #111;
		border-radius: 999px;
		min-width: 2px;
	}

	.bar-value {
		width: 2rem;
		text-align: right;
		font-size: 0.9rem;
		color: #6b7280;
	}

	.recent {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.recent li {
		font-size: 0.9rem;
		color: #374151;
		padding: 0.3rem 0;
		border-bottom: 1px solid #f3f4f6;
	}

	.muted {
		color: #9ca3af;
	}

	.small {
		font-size: 0.85rem;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
	}

	@media (max-width: 640px) {
		.panels {
			grid-template-columns: 1fr;
		}
	}
</style>
