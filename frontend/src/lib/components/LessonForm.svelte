<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';

	// When set, the form loads that lesson and saves via PUT (edit mode).
	export let lessonId: string | null = null;

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
	interface RawBlock {
		type: string;
		value?: string;
		words?: string[];
		[key: string]: unknown;
	}

	// Editor-side block shapes (text / vocab as comma string / raw JSON fallback).
	type EditorBlock =
		| { kind: 'text'; value: string }
		| { kind: 'vocab_list'; words: string }
		| { kind: 'raw'; json: string };

	let languages: Language[] = [];
	let levels: Level[] = [];

	let languageCode = '';
	let difficultyId: number | null = null;
	let title = '';
	let status: 'draft' | 'published' = 'draft';
	let blocks: EditorBlock[] = [];

	let loading = true;
	let saving = false;
	let error = '';

	const isEdit = !!lessonId;

	function toEditorBlock(b: RawBlock): EditorBlock {
		if (b.type === 'text') return { kind: 'text', value: b.value ?? '' };
		if (b.type === 'vocab_list')
			return { kind: 'vocab_list', words: (b.words ?? []).join(', ') };
		return { kind: 'raw', json: JSON.stringify(b, null, 2) };
	}

	function toRawBlock(b: EditorBlock): RawBlock {
		if (b.kind === 'text') return { type: 'text', value: b.value };
		if (b.kind === 'vocab_list')
			return {
				type: 'vocab_list',
				words: b.words
					.split(',')
					.map((w) => w.trim())
					.filter(Boolean)
			};
		return JSON.parse(b.json) as RawBlock;
	}

	async function loadLevels(code: string) {
		if (!code) {
			levels = [];
			return;
		}
		levels = await api.get<Level[]>(`/learn/${code}/levels`);
		// Drop a stale difficulty selection that no longer belongs to this language.
		if (!levels.some((l) => l.id === difficultyId)) difficultyId = null;
	}

	async function onLanguageChange() {
		difficultyId = null;
		await loadLevels(languageCode);
	}

	function addBlock(kind: EditorBlock['kind']) {
		if (kind === 'text') blocks = [...blocks, { kind: 'text', value: '' }];
		else if (kind === 'vocab_list') blocks = [...blocks, { kind: 'vocab_list', words: '' }];
		else blocks = [...blocks, { kind: 'raw', json: '{\n  "type": ""\n}' }];
	}

	function removeBlock(i: number) {
		blocks = blocks.filter((_, idx) => idx !== i);
	}

	function moveBlock(i: number, dir: -1 | 1) {
		const j = i + dir;
		if (j < 0 || j >= blocks.length) return;
		const next = [...blocks];
		[next[i], next[j]] = [next[j], next[i]];
		blocks = next;
	}

	async function save() {
		error = '';
		const lang = languages.find((l) => l.code === languageCode);
		if (!lang) {
			error = '請選擇語言';
			return;
		}
		if (!difficultyId) {
			error = '請選擇難度';
			return;
		}
		if (!title.trim()) {
			error = '請輸入標題';
			return;
		}

		let content: RawBlock[];
		try {
			content = blocks.map(toRawBlock);
		} catch {
			error = '有內容區塊的 JSON 格式錯誤，請檢查';
			return;
		}

		saving = true;
		try {
			if (isEdit) {
				await api.put(`/admin/lessons/${lessonId}`, {
					title,
					difficulty_id: difficultyId,
					content,
					status
				});
			} else {
				await api.post('/admin/lessons', {
					language_id: lang.id,
					difficulty_id: difficultyId,
					title,
					content,
					status
				});
			}
			goto('/admin/lessons');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '儲存失敗';
		} finally {
			saving = false;
		}
	}

	onMount(async () => {
		try {
			languages = await api.get<Language[]>('/learn/languages');
			if (isEdit) {
				const lesson = await api.get<{
					language_id: number;
					difficulty_id: number;
					title: string;
					status: 'draft' | 'published';
					content: RawBlock[];
				}>(`/admin/lessons/${lessonId}`);
				title = lesson.title;
				status = lesson.status;
				blocks = (lesson.content ?? []).map(toEditorBlock);
				difficultyId = lesson.difficulty_id;
				const lang = languages.find((l) => l.id === lesson.language_id);
				languageCode = lang?.code ?? '';
				await loadLevels(languageCode);
				difficultyId = lesson.difficulty_id; // keep after loadLevels reset guard
			}
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	});
</script>

{#if loading}
	<p class="muted">載入中…</p>
{:else}
	<form class="lesson-form" on:submit|preventDefault={save}>
		{#if error}<p class="error">{error}</p>{/if}

		<div class="row">
			<label>
				語言
				<select bind:value={languageCode} on:change={onLanguageChange} disabled={isEdit}>
					<option value="" disabled>選擇語言</option>
					{#each languages as lang (lang.id)}
						<option value={lang.code}>{lang.name_zh}</option>
					{/each}
				</select>
			</label>

			<label>
				難度
				<select bind:value={difficultyId} disabled={!languageCode}>
					<option value={null} disabled>選擇難度</option>
					{#each levels as level (level.id)}
						<option value={level.id}>{level.label_zh}</option>
					{/each}
				</select>
			</label>

			<label>
				狀態
				<select bind:value={status}>
					<option value="draft">草稿</option>
					<option value="published">發布</option>
				</select>
			</label>
		</div>

		<label class="block-label">
			標題
			<input type="text" bind:value={title} placeholder="例如：Greetings 打招呼" />
		</label>

		<div class="content-editor">
			<div class="editor-head">
				<h3>課程內容</h3>
				<div class="add-buttons">
					<button type="button" on:click={() => addBlock('text')}>+ 文字</button>
					<button type="button" on:click={() => addBlock('vocab_list')}>+ 單字表</button>
					<button type="button" on:click={() => addBlock('raw')}>+ 進階(JSON)</button>
				</div>
			</div>

			{#if blocks.length === 0}
				<p class="muted small">尚無內容區塊，用上方按鈕新增。</p>
			{/if}

			{#each blocks as block, i (i)}
				<div class="block">
					<div class="block-toolbar">
						<span class="block-type">
							{block.kind === 'text' ? '文字' : block.kind === 'vocab_list' ? '單字表' : '進階 JSON'}
						</span>
						<div class="block-actions">
							<button type="button" on:click={() => moveBlock(i, -1)} title="上移">↑</button>
							<button type="button" on:click={() => moveBlock(i, 1)} title="下移">↓</button>
							<button type="button" class="danger" on:click={() => removeBlock(i)} title="刪除">✕</button>
						</div>
					</div>

					{#if block.kind === 'text'}
						<textarea bind:value={block.value} rows="3" placeholder="輸入說明文字…"></textarea>
					{:else if block.kind === 'vocab_list'}
						<input
							type="text"
							bind:value={block.words}
							placeholder="以逗號分隔，例如：hello, hi, morning"
						/>
					{:else}
						<textarea bind:value={block.json} rows="5" class="mono"></textarea>
					{/if}
				</div>
			{/each}
		</div>

		<div class="form-actions">
			<button type="submit" class="btn-primary" disabled={saving}>
				{saving ? '儲存中…' : isEdit ? '更新課程' : '建立課程'}
			</button>
			<a href="/admin/lessons" class="btn-cancel">取消</a>
		</div>
	</form>
{/if}

<style>
	.lesson-form {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.row {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.row label {
		flex: 1;
		min-width: 140px;
	}

	label {
		display: block;
		font-size: 0.9rem;
		color: #374151;
	}

	.block-label {
		display: block;
	}

	select,
	input,
	textarea {
		display: block;
		width: 100%;
		padding: 0.55rem;
		margin-top: 0.3rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 0.95rem;
		box-sizing: border-box;
		font-family: inherit;
	}

	select:disabled {
		background: #f3f4f6;
		color: #6b7280;
	}

	.mono {
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.85rem;
	}

	.content-editor {
		border: 1px solid #e5e7eb;
		border-radius: 10px;
		padding: 1rem;
	}

	.editor-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}

	.editor-head h3 {
		font-size: 1rem;
		color: #111;
	}

	.add-buttons {
		display: flex;
		gap: 0.5rem;
	}

	.add-buttons button {
		background: #f3f4f6;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		padding: 0.35rem 0.7rem;
		font-size: 0.85rem;
		cursor: pointer;
	}

	.block {
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 0.8rem;
		margin-bottom: 0.8rem;
		background: #fafafa;
	}

	.block-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.5rem;
	}

	.block-type {
		font-size: 0.8rem;
		font-weight: 600;
		color: #6b7280;
	}

	.block-actions {
		display: flex;
		gap: 0.3rem;
	}

	.block-actions button {
		background: white;
		border: 1px solid #d1d5db;
		border-radius: 5px;
		width: 26px;
		height: 26px;
		cursor: pointer;
		font-size: 0.8rem;
		line-height: 1;
	}

	.block-actions .danger {
		color: #dc2626;
	}

	.form-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.7rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
	}

	.btn-primary:disabled {
		opacity: 0.5;
	}

	.btn-cancel {
		color: #6b7280;
		text-decoration: none;
		font-size: 0.9rem;
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
