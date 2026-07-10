<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';

	interface Language {
		id: number;
		code: string;
		name_zh: string;
	}

	let languages: Language[] = [];
	let title = '';
	let languageId: number | null = null;
	let saving = false;
	let error = '';

	async function save() {
		error = '';
		if (!title.trim()) return (error = '請輸入卡組名稱');
		if (!languageId) return (error = '請選擇語言');
		saving = true;
		try {
			const deck = await api.post<{ id: string }>('/flashcards', {
				title,
				language_id: languageId
			});
			goto(`/flashcards/${deck.id}`);
		} catch (err) {
			error = (err as { detail?: string })?.detail || '建立失敗';
		} finally {
			saving = false;
		}
	}

	onMount(async () => {
		languages = await api.get<Language[]>('/learn/languages');
	});
</script>

<svelte:head>
	<title>建立卡組 — Heniiii</title>
</svelte:head>

<section class="new-deck">
	<a class="back" href="/flashcards">← 我的單字卡</a>
	<h1>建立卡組</h1>

	<form on:submit|preventDefault={save}>
		{#if error}<p class="error">{error}</p>{/if}

		<label>
			卡組名稱
			<input type="text" bind:value={title} placeholder="例如：旅遊英文" />
		</label>

		<label>
			語言
			<select bind:value={languageId}>
				<option value={null} disabled>選擇語言</option>
				{#each languages as lang (lang.id)}
					<option value={lang.id}>{lang.name_zh}</option>
				{/each}
			</select>
		</label>

		<div class="actions">
			<button type="submit" class="btn-primary" disabled={saving}>
				{saving ? '建立中…' : '建立'}
			</button>
			<a href="/flashcards" class="btn-cancel">取消</a>
		</div>
	</form>
</section>

<style>
	.new-deck {
		max-width: 480px;
		margin: 0 auto;
	}

	.back {
		display: inline-block;
		margin-bottom: 1rem;
		color: #6b7280;
		text-decoration: none;
		font-size: 0.9rem;
	}
	.back:hover {
		color: #111;
	}

	h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
		margin-bottom: 1.5rem;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}

	label {
		display: block;
		font-size: 0.9rem;
		color: #374151;
	}

	input,
	select {
		display: block;
		width: 100%;
		padding: 0.6rem;
		margin-top: 0.3rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 1rem;
		box-sizing: border-box;
		font-family: inherit;
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

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
	}
</style>
