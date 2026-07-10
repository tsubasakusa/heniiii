<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';

	interface UserRow {
		id: string;
		email: string;
		display_name: string;
		role: string;
		created_at: string;
	}

	const ROLE_LABEL: Record<string, string> = { admin: '管理員', editor: '編輯', user: '一般' };

	let users: UserRow[] = [];
	let loading = true;
	let error = '';

	onMount(async () => {
		try {
			users = await api.get<UserRow[]>('/admin/users');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗（需管理員權限）';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>使用者管理 — Heniiii 後台</title>
</svelte:head>

<section class="admin">
	<h1>使用者管理</h1>

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else}
		<table>
			<thead>
				<tr>
					<th>名稱</th>
					<th>Email</th>
					<th>角色</th>
					<th>註冊日期</th>
				</tr>
			</thead>
			<tbody>
				{#each users as u (u.id)}
					<tr>
						<td>{u.display_name}</td>
						<td class="muted">{u.email}</td>
						<td><span class="badge {u.role}">{ROLE_LABEL[u.role] ?? u.role}</span></td>
						<td class="muted">{u.created_at.slice(0, 10)}</td>
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

	h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
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

	.badge {
		font-size: 0.8rem;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		background: #f3f4f6;
		color: #374151;
	}
	.badge.admin {
		background: #fee2e2;
		color: #991b1b;
	}
	.badge.editor {
		background: #dbeafe;
		color: #1e40af;
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
