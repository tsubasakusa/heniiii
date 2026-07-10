<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface Language {
		id: number;
		code: string;
		name_zh: string;
	}
	interface LessonSummary {
		id: string;
		title: string;
		language_id: number;
		difficulty_id: number;
		status: string;
	}

	let languages: Language[] = [];
	let lessons: LessonSummary[] = [];
	let filterLang = '';
	let loading = true;
	let error = '';

	function langName(id: number): string {
		return languages.find((l) => l.id === id)?.name_zh ?? String(id);
	}

	async function loadLessons() {
		loading = true;
		error = '';
		try {
			const q = filterLang ? `?lang=${filterLang}` : '';
			lessons = await api.get<LessonSummary[]>(`/admin/lessons${q}`);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	async function remove(lesson: LessonSummary) {
		if (!confirm(`確定要刪除「${lesson.title}」？`)) return;
		try {
			await api.delete(`/admin/lessons/${lesson.id}`);
			lessons = lessons.filter((l) => l.id !== lesson.id);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '刪除失敗';
		}
	}

	onMount(async () => {
		languages = await api.get<Language[]>('/learn/languages');
		await loadLessons();
	});
</script>

<svelte:head>
	<title>課程管理 — Heniiii 後台</title>
</svelte:head>

<section class="admin">
	<header class="head">
		<div>
			<h1>課程管理</h1>
			<p>建立、編輯與發布分級課程。</p>
		</div>
		<a href="/admin/lessons/new" class="btn-primary">+ 新增課程</a>
	</header>

	<div class="filter">
		<label>
			語言篩選
			<select bind:value={filterLang} on:change={loadLessons}>
				<option value="">全部</option>
				{#each languages as lang (lang.id)}
					<option value={lang.code}>{lang.name_zh}</option>
				{/each}
			</select>
		</label>
	</div>

	{#if error}<p class="error">{error}</p>{/if}

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if lessons.length === 0}
		<p class="muted">目前沒有課程。</p>
	{:else}
		<table>
			<thead>
				<tr>
					<th>標題</th>
					<th>語言</th>
					<th>狀態</th>
					<th class="right">操作</th>
				</tr>
			</thead>
			<tbody>
				{#each lessons as lesson (lesson.id)}
					<tr>
						<td>{lesson.title}</td>
						<td>{langName(lesson.language_id)}</td>
						<td>
							<span class="badge {lesson.status}">
								{lesson.status === 'published' ? '已發布' : '草稿'}
							</span>
						</td>
						<td class="right actions">
							<a href={`/admin/lessons/${lesson.id}/edit`}>編輯</a>
							<button type="button" class="link-danger" on:click={() => remove(lesson)}>刪除</button>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</section>

<style>
	.admin {
		max-width: 860px;
		margin: 0 auto;
	}

	.head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	.head h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
	}

	.head p {
		color: #6b7280;
		margin-top: 0.2rem;
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

	.filter {
		margin-bottom: 1rem;
	}

	.filter label {
		font-size: 0.85rem;
		color: #6b7280;
	}

	.filter select {
		margin-left: 0.5rem;
		padding: 0.4rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th,
	td {
		text-align: left;
		padding: 0.8rem 0.6rem;
		border-bottom: 1px solid #e5e7eb;
		font-size: 0.95rem;
	}

	th {
		font-size: 0.8rem;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.right {
		text-align: right;
	}

	.badge {
		font-size: 0.8rem;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
	}

	.badge.published {
		background: #dcfce7;
		color: #166534;
	}

	.badge.draft {
		background: #f3f4f6;
		color: #6b7280;
	}

	.actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
	}

	.actions a {
		color: #111;
		text-decoration: none;
		font-weight: 600;
	}

	.link-danger {
		background: none;
		border: none;
		color: #dc2626;
		cursor: pointer;
		font-size: 0.95rem;
		padding: 0;
	}

	.muted {
		color: #9ca3af;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		margin-bottom: 1rem;
	}
</style>
