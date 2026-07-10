<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface Level {
		id: number;
		slug: string;
		label_zh: string;
		sort_order: number;
	}

	interface LessonSummary {
		id: string;
		title: string;
		language_id: number;
		difficulty_id: number;
		status: string;
	}

	const LANG_NAMES: Record<string, string> = { en: '英文', ja: '日文', tailo: '台語' };

	let lang = '';
	let langName = '';
	let levels: Level[] = [];
	let lessons: LessonSummary[] = [];
	let loading = true;
	let error = '';

	function lessonsForLevel(levelId: number): LessonSummary[] {
		return lessons.filter((l) => l.difficulty_id === levelId);
	}

	async function load(code: string) {
		loading = true;
		error = '';
		try {
			[levels, lessons] = await Promise.all([
				api.get<Level[]>(`/learn/${code}/levels`),
				api.get<LessonSummary[]>(`/learn/${code}/lessons`)
			]);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	// React to /learn/en -> /learn/ja navigation (same component, new param).
	$: lang = $page.params.lang ?? '';
	$: langName = LANG_NAMES[lang] ?? lang;

	onMount(() => {
		load(lang);
	});

	let lastLoaded = '';
	$: if (lang && lang !== lastLoaded) {
		lastLoaded = lang;
		load(lang);
	}
</script>

<svelte:head>
	<title>{langName}課程 — Heniiii</title>
</svelte:head>

<section class="learn">
	<header class="head">
		<h1>{langName}</h1>
		<p>選擇適合的難度，開始分級學習。</p>
		<a class="vocab-link" href={`/learn/${lang}/vocabulary`}>📖 {langName}單字表 →</a>
	</header>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if levels.length === 0}
		<p class="muted">目前尚無此語言的課程分級。</p>
	{:else}
		{#each levels as level (level.id)}
			<div class="level">
				<div class="level-head">
					<h2>{level.label_zh}</h2>
					<span class="count">{lessonsForLevel(level.id).length} 堂課</span>
				</div>

				{#if lessonsForLevel(level.id).length === 0}
					<p class="muted small">尚無課程</p>
				{:else}
					<ul class="lessons">
						{#each lessonsForLevel(level.id) as lesson (lesson.id)}
							<li>
								<a href={`/learn/${lang}/lesson/${lesson.id}`}>
									<span class="title">{lesson.title}</span>
									<span class="arrow">→</span>
								</a>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		{/each}
	{/if}
</section>

<style>
	.learn {
		max-width: 760px;
		margin: 0 auto;
	}

	.head {
		margin-bottom: 2.5rem;
	}

	.head h1 {
		font-size: 2.4rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 0.3rem;
	}

	.head p {
		color: #6b7280;
	}

	.vocab-link {
		display: inline-block;
		margin-top: 0.8rem;
		color: #111;
		font-weight: 600;
		text-decoration: none;
		font-size: 0.95rem;
	}

	.vocab-link:hover {
		text-decoration: underline;
	}

	.level {
		margin-bottom: 2rem;
	}

	.level-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		border-bottom: 2px solid #111;
		padding-bottom: 0.4rem;
		margin-bottom: 0.8rem;
	}

	.level-head h2 {
		font-size: 1.3rem;
		font-weight: 700;
		color: #111;
	}

	.count {
		font-size: 0.85rem;
		color: #9ca3af;
	}

	.lessons {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.lessons a {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.9rem 1.1rem;
		border: 1px solid #e5e7eb;
		border-radius: 10px;
		text-decoration: none;
		color: #111;
		transition: border-color 0.15s, transform 0.15s;
	}

	.lessons a:hover {
		border-color: #111;
		transform: translateX(2px);
	}

	.title {
		font-weight: 600;
	}

	.arrow {
		color: #9ca3af;
	}

	.muted {
		color: #9ca3af;
	}

	.small {
		font-size: 0.9rem;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
	}
</style>
