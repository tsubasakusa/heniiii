<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { api } from '$lib/api/client';

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

	export let languages: Language[] = [];
	export let vocab: Vocab | null = null; // edit mode when provided
	export let defaultLangCode = '';

	const dispatch = createEventDispatcher<{ saved: void; cancel: void }>();
	const isEdit = !!vocab;

	let languageCode = '';
	let difficultyId: number | null = null;
	let word = '';
	let pronunciation = '';
	let meaningZh = '';
	let exampleSentence = '';
	let audioUrl = '';

	let levels: Level[] = [];
	let saving = false;
	let error = '';

	async function loadLevels(code: string) {
		if (!code) {
			levels = [];
			return;
		}
		levels = await api.get<Level[]>(`/learn/${code}/levels`);
		if (!levels.some((l) => l.id === difficultyId)) difficultyId = null;
	}

	async function onLanguageChange() {
		difficultyId = null;
		await loadLevels(languageCode);
	}

	async function save() {
		error = '';
		const lang = languages.find((l) => l.code === languageCode);
		if (!lang) return (error = '請選擇語言');
		if (!difficultyId) return (error = '請選擇難度');
		if (!word.trim()) return (error = '請輸入單字');
		if (!pronunciation.trim()) return (error = '請輸入發音');
		if (!meaningZh.trim()) return (error = '請輸入中文意思');

		const payload = {
			difficulty_id: difficultyId,
			word,
			pronunciation,
			meaning_zh: meaningZh,
			example_sentence: exampleSentence || null,
			audio_url: audioUrl || null
		};

		saving = true;
		try {
			if (isEdit && vocab) {
				await api.put(`/admin/vocabulary/${vocab.id}`, payload);
			} else {
				await api.post('/admin/vocabulary', { language_id: lang.id, ...payload });
			}
			dispatch('saved');
		} catch (err) {
			error = (err as { detail?: string })?.detail || '儲存失敗';
		} finally {
			saving = false;
		}
	}

	onMount(async () => {
		if (vocab) {
			languageCode = languages.find((l) => l.id === vocab.language_id)?.code ?? '';
			word = vocab.word;
			pronunciation = vocab.pronunciation;
			meaningZh = vocab.meaning_zh;
			exampleSentence = vocab.example_sentence ?? '';
			audioUrl = vocab.audio_url ?? '';
			difficultyId = vocab.difficulty_id;
			await loadLevels(languageCode);
			difficultyId = vocab.difficulty_id;
		} else if (defaultLangCode) {
			languageCode = defaultLangCode;
			await loadLevels(languageCode);
		}
	});
</script>

<form class="vocab-form" on:submit|preventDefault={save}>
	<div class="head">
		<strong>{isEdit ? '編輯單字' : '新增單字'}</strong>
	</div>

	{#if error}<p class="error">{error}</p>{/if}

	<div class="grid">
		<label>
			語言
			<select bind:value={languageCode} on:change={onLanguageChange} disabled={isEdit}>
				<option value="" disabled>選擇</option>
				{#each languages as lang (lang.id)}
					<option value={lang.code}>{lang.name_zh}</option>
				{/each}
			</select>
		</label>

		<label>
			難度
			<select bind:value={difficultyId} disabled={!languageCode}>
				<option value={null} disabled>選擇</option>
				{#each levels as level (level.id)}
					<option value={level.id}>{level.label_zh}</option>
				{/each}
			</select>
		</label>

		<label>
			單字
			<input type="text" bind:value={word} placeholder="hello" />
		</label>

		<label>
			發音
			<input type="text" bind:value={pronunciation} placeholder="音標 / 假名 / 台羅" />
		</label>

		<label>
			中文意思
			<input type="text" bind:value={meaningZh} placeholder="你好" />
		</label>

		<label>
			音檔網址(選填)
			<input type="text" bind:value={audioUrl} placeholder="https://…" />
		</label>
	</div>

	<label class="full">
		例句(選填)
		<input type="text" bind:value={exampleSentence} placeholder="Hello, how are you?" />
	</label>

	<div class="actions">
		<button type="submit" class="btn-primary" disabled={saving}>
			{saving ? '儲存中…' : isEdit ? '更新' : '新增'}
		</button>
		<button type="button" class="btn-cancel" on:click={() => dispatch('cancel')}>取消</button>
	</div>
</form>

<style>
	.vocab-form {
		border: 1px solid #e5e7eb;
		border-radius: 10px;
		padding: 1.2rem;
		background: #fafafa;
		margin-bottom: 1.5rem;
	}

	.head {
		margin-bottom: 1rem;
		font-size: 1rem;
		color: #111;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.8rem;
	}

	label {
		display: block;
		font-size: 0.85rem;
		color: #374151;
	}

	.full {
		margin-top: 0.8rem;
	}

	select,
	input {
		display: block;
		width: 100%;
		padding: 0.5rem;
		margin-top: 0.25rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 0.9rem;
		box-sizing: border-box;
		font-family: inherit;
	}

	select:disabled {
		background: #f3f4f6;
		color: #6b7280;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-top: 1rem;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.55rem 1.5rem;
		border: none;
		border-radius: 8px;
		font-size: 0.95rem;
		font-weight: 600;
		cursor: pointer;
	}

	.btn-primary:disabled {
		opacity: 0.5;
	}

	.btn-cancel {
		background: none;
		border: none;
		color: #6b7280;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.5rem 0.9rem;
		border-radius: 8px;
		margin-bottom: 0.8rem;
	}

	@media (max-width: 640px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
