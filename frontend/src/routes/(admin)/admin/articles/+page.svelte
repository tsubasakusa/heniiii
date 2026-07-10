<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface Article {
		id: string;
		title: string;
		slug: string;
		status: string;
		language_id: number | null;
	}

	const LANG_BY_ID: Record<number, string> = { 1: '英文', 2: '日文', 3: '台語' };

	let articles: Article[] = [];
	let loading = true;
	let error = '';

	async function load() {
		loading = true;
		try {
			articles = await api.get<Article[]>('/admin/articles');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	async function remove(a: Article) {
		if (!confirm(`刪除「${a.title}」？`)) return;
		try {
			await api.delete(`/admin/articles/${a.id}`);
			articles = articles.filter((x) => x.id !== a.id);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '刪除失敗';
		}
	}

	onMount(load);
</script>

<svelte:head>
	<title>文章管理 — Heniiii 後台</title>
</svelte:head>

<section class="admin">
	<header class="head">
		<div>
			<h1>文章管理</h1>
			<p>撰寫與發布部落格文章。</p>
		</div>
		<a href="/admin/articles/new" class="btn-primary">+ 新增文章</a>
	</header>

	{#if error}<p class="error">{error}</p>{/if}

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if articles.length === 0}
		<p class="muted">目前沒有文章。</p>
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
				{#each articles as a (a.id)}
					<tr>
						<td>{a.title}</td>
						<td>{a.language_id ? (LANG_BY_ID[a.language_id] ?? '') : '通用'}</td>
						<td>
							<span class="badge {a.status}">{a.status === 'published' ? '已發布' : '草稿'}</span>
						</td>
						<td class="right actions">
							<a href={`/admin/articles/${a.id}/edit`}>編輯</a>
							<button class="link-danger" on:click={() => remove(a)}>刪除</button>
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
