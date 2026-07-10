<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';

	export let articleId: string | null = null;

	interface Language {
		id: number;
		code: string;
		name_zh: string;
	}

	let languages: Language[] = [];
	let title = '';
	let slug = '';
	let languageId: number | null = null;
	let status: 'draft' | 'published' = 'draft';
	let tagsText = '';
	let coverImageUrl = '';
	let content = '';

	let loading = true;
	let saving = false;
	let error = '';

	const isEdit = !!articleId;

	async function save() {
		error = '';
		if (!title.trim()) return (error = '請輸入標題');

		const payload = {
			title,
			slug: slug || null,
			content,
			cover_image_url: coverImageUrl || null,
			language_id: languageId,
			tags: tagsText
				.split(',')
				.map((t) => t.trim())
				.filter(Boolean),
			status
		};

		saving = true;
		try {
			if (isEdit) {
				await api.put(`/admin/articles/${articleId}`, payload);
			} else {
				await api.post('/admin/articles', payload);
			}
			goto('/admin/articles');
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
				const a = await api.get<{
					title: string;
					slug: string;
					content: string;
					cover_image_url: string | null;
					language_id: number | null;
					tags: string[];
					status: 'draft' | 'published';
				}>(`/admin/articles/${articleId}`);
				title = a.title;
				slug = a.slug;
				content = a.content;
				coverImageUrl = a.cover_image_url ?? '';
				languageId = a.language_id;
				tagsText = (a.tags ?? []).join(', ');
				status = a.status;
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
	<form class="article-form" on:submit|preventDefault={save}>
		{#if error}<p class="error">{error}</p>{/if}

		<label>
			標題
			<input type="text" bind:value={title} placeholder="文章標題" />
		</label>

		<div class="row">
			<label>
				網址 slug（選填，留空自動產生）
				<input type="text" bind:value={slug} placeholder="my-article" />
			</label>
			<label>
				語言
				<select bind:value={languageId}>
					<option value={null}>通用</option>
					{#each languages as lang (lang.id)}
						<option value={lang.id}>{lang.name_zh}</option>
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

		<div class="row">
			<label>
				標籤（逗號分隔）
				<input type="text" bind:value={tagsText} placeholder="學習, 文法" />
			</label>
			<label>
				封面圖網址（選填）
				<input type="text" bind:value={coverImageUrl} placeholder="https://…" />
			</label>
		</div>

		<label>
			內文（Markdown）
			<textarea bind:value={content} rows="14" placeholder="# 標題&#10;&#10;支援 **粗體**、清單、連結…"></textarea>
		</label>

		<div class="actions">
			<button type="submit" class="btn-primary" disabled={saving}>
				{saving ? '儲存中…' : isEdit ? '更新文章' : '建立文章'}
			</button>
			<a href="/admin/articles" class="btn-cancel">取消</a>
		</div>
	</form>
{/if}

<style>
	.article-form {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}

	.row {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.row label {
		flex: 1;
		min-width: 150px;
	}

	label {
		display: block;
		font-size: 0.9rem;
		color: #374151;
	}

	input,
	select,
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

	textarea {
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.9rem;
		line-height: 1.6;
	}

	.actions {
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

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
	}
</style>
