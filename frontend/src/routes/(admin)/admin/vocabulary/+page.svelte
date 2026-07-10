<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import VocabForm from '$lib/components/VocabForm.svelte';

	interface Language {
		id: number;
		code: string;
		name_zh: string;
	}
	interface Level {
		id: number;
		slug: string;
		label_zh: string;
	}
	interface Vocab {
		id: string;
		language_id: number;
		difficulty_id: number;
		word: string;
		pronunciation: string;
		meaning_zh: string;
		example_sentence: string | null;
		audio_url: string | null;
	}

	let languages: Language[] = [];
	let levels: Level[] = [];
	let vocab: Vocab[] = [];

	let filterLang = 'en';
	let filterLevel = '';
	let loading = true;
	let error = '';

	// null = closed; 'new' = create form; otherwise the vocab being edited.
	let editing: Vocab | 'new' | null = null;

	function levelLabel(id: number): string {
		return levels.find((l) => l.id === id)?.label_zh ?? '';
	}

	async function loadVocab() {
		loading = true;
		error = '';
		try {
			const q = filterLevel ? `?lang=${filterLang}&level=${filterLevel}` : `?lang=${filterLang}`;
			[levels, vocab] = await Promise.all([
				api.get<Level[]>(`/learn/${filterLang}/levels`),
				api.get<Vocab[]>(`/admin/vocabulary${q}`)
			]);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	async function onFilterChange() {
		filterLevel = '';
		editing = null;
		await loadVocab();
	}

	async function onSaved() {
		editing = null;
		await loadVocab();
	}

	async function remove(v: Vocab) {
		if (!confirm(`確定要刪除「${v.word}」？`)) return;
		try {
			await api.delete(`/admin/vocabulary/${v.id}`);
			vocab = vocab.filter((x) => x.id !== v.id);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '刪除失敗';
		}
	}

	onMount(async () => {
		languages = await api.get<Language[]>('/learn/languages');
		await loadVocab();
	});
</script>

<svelte:head>
	<title>單字管理 — Heniiii 後台</title>
</svelte:head>

<section class="admin">
	<header class="head">
		<div>
			<h1>單字管理</h1>
			<p>維護各語言分級的單字庫。</p>
		</div>
		{#if editing === null}
			<button class="btn-primary" on:click={() => (editing = 'new')}>+ 新增單字</button>
		{/if}
	</header>

	<div class="filters">
		<label>
			語言
			<select bind:value={filterLang} on:change={onFilterChange}>
				{#each languages as lang (lang.id)}
					<option value={lang.code}>{lang.name_zh}</option>
				{/each}
			</select>
		</label>
		<label>
			難度
			<select bind:value={filterLevel} on:change={loadVocab} disabled={editing !== null}>
				<option value="">全部</option>
				{#each levels as level (level.id)}
					<option value={String(level.id)}>{level.label_zh}</option>
				{/each}
			</select>
		</label>
	</div>

	{#if editing === 'new'}
		<VocabForm {languages} defaultLangCode={filterLang} on:saved={onSaved} on:cancel={() => (editing = null)} />
	{:else if editing}
		<VocabForm {languages} vocab={editing} on:saved={onSaved} on:cancel={() => (editing = null)} />
	{/if}

	{#if error}<p class="error">{error}</p>{/if}

	{#if loading}
		<p class="muted">載入中…</p>
	{:else if vocab.length === 0}
		<p class="muted">此語言目前沒有單字。</p>
	{:else}
		<table>
			<thead>
				<tr>
					<th>單字</th>
					<th>發音</th>
					<th>中文意思</th>
					<th>難度</th>
					<th class="right">操作</th>
				</tr>
			</thead>
			<tbody>
				{#each vocab as v (v.id)}
					<tr>
						<td class="word">{v.word}</td>
						<td class="muted">{v.pronunciation}</td>
						<td>{v.meaning_zh}</td>
						<td>{levelLabel(v.difficulty_id)}</td>
						<td class="right actions">
							<button type="button" on:click={() => (editing = v)}>編輯</button>
							<button type="button" class="link-danger" on:click={() => remove(v)}>刪除</button>
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
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		white-space: nowrap;
	}

	.filters {
		display: flex;
		gap: 1.5rem;
		margin-bottom: 1rem;
	}

	.filters label {
		font-size: 0.85rem;
		color: #6b7280;
	}

	.filters select {
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
		padding: 0.7rem 0.6rem;
		border-bottom: 1px solid #e5e7eb;
		font-size: 0.95rem;
	}

	th {
		font-size: 0.8rem;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.word {
		font-weight: 600;
		color: #111;
	}

	.muted {
		color: #9ca3af;
	}

	.right {
		text-align: right;
	}

	.actions {
		display: flex;
		gap: 0.8rem;
		justify-content: flex-end;
	}

	.actions button {
		background: none;
		border: none;
		cursor: pointer;
		font-size: 0.9rem;
		padding: 0;
		color: #111;
		font-weight: 600;
	}

	.link-danger {
		color: #dc2626 !important;
		font-weight: 400 !important;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		margin-bottom: 1rem;
	}
</style>
