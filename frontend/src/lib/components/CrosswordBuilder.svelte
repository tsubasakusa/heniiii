<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';

	export let puzzleId: string | null = null;

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
	interface Slot {
		number: number;
		row: number;
		col: number;
		length: number;
	}

	let languages: Language[] = [];
	let levels: Level[] = [];
	let languageCode = '';
	let difficultyId: number | null = null;
	let publishDate = '';
	let status: 'draft' | 'scheduled' | 'published' = 'draft';

	let rows = 5;
	let cols = 5;
	let grid: string[][] = makeGrid(5, 5);
	// clue text keyed by `a-<n>` / `d-<n>`
	let clueText: Record<string, string> = {};

	let loading = true;
	let saving = false;
	let error = '';

	const isEdit = !!puzzleId;

	function makeGrid(r: number, c: number, from: string[][] = []): string[][] {
		return Array.from({ length: r }, (_, i) =>
			Array.from({ length: c }, (_, j) => from[i]?.[j] ?? '')
		);
	}

	function resize() {
		rows = Math.max(1, Math.min(12, rows));
		cols = Math.max(1, Math.min(12, cols));
		grid = makeGrid(rows, cols, grid);
	}

	function onCell(r: number, c: number, e: Event) {
		const v = (e.target as HTMLInputElement).value.slice(-1).toUpperCase();
		grid[r][c] = v.replace(/[^A-Za-z぀-ヿ一-鿿]/, '');
		grid = grid;
	}

	// --- auto numbering + slot detection (standard crossword rules) ---
	// Pure function with explicit deps so Svelte re-runs it whenever the grid
	// changes (a `$:` block that only touched grid via a helper would not react).
	function computeNumbering(g: string[][], r0: number, c0: number) {
		const on = (r: number, c: number) =>
			r >= 0 && c >= 0 && r < r0 && c < c0 && g[r][c] !== '';
		const numberAt: Record<string, number> = {};
		const across: Slot[] = [];
		const down: Slot[] = [];
		let n = 0;
		for (let r = 0; r < r0; r++) {
			for (let c = 0; c < c0; c++) {
				if (!on(r, c)) continue;
				const startsAcross = !on(r, c - 1) && on(r, c + 1);
				const startsDown = !on(r - 1, c) && on(r + 1, c);
				if (startsAcross || startsDown) {
					n++;
					numberAt[`${r},${c}`] = n;
					if (startsAcross) {
						let len = 0;
						let cc = c;
						while (on(r, cc)) {
							len++;
							cc++;
						}
						across.push({ number: n, row: r, col: c, length: len });
					}
					if (startsDown) {
						let len = 0;
						let rr = r;
						while (on(rr, c)) {
							len++;
							rr++;
						}
						down.push({ number: n, row: r, col: c, length: len });
					}
				}
			}
		}
		return { numberAt, across, down };
	}

	$: numbering = computeNumbering(grid, rows, cols);

	async function loadLevels(code: string) {
		if (!code) return (levels = []);
		levels = await api.get<Level[]>(`/learn/${code}/levels`);
		if (!levels.some((l) => l.id === difficultyId)) difficultyId = null;
	}

	async function onLanguageChange() {
		difficultyId = null;
		await loadLevels(languageCode);
	}

	function buildPayload() {
		const cells: { r: number; c: number; answer: string; number?: number }[] = [];
		for (let r = 0; r < rows; r++) {
			for (let c = 0; c < cols; c++) {
				if (grid[r][c] === '') continue;
				const cell: { r: number; c: number; answer: string; number?: number } = {
					r,
					c,
					answer: grid[r][c].toUpperCase()
				};
				const num = numbering.numberAt[`${r},${c}`];
				if (num) cell.number = num;
				cells.push(cell);
			}
		}
		const lang = languages.find((l) => l.code === languageCode);
		return {
			language_id: lang?.id,
			difficulty_id: difficultyId,
			publish_date: publishDate,
			grid_data: { rows, cols, cells },
			clues: {
				across: numbering.across.map((s) => ({
					number: s.number,
					row: s.row,
					col: s.col,
					length: s.length,
					clue: clueText[`a-${s.number}`] ?? ''
				})),
				down: numbering.down.map((s) => ({
					number: s.number,
					row: s.row,
					col: s.col,
					length: s.length,
					clue: clueText[`d-${s.number}`] ?? ''
				}))
			},
			status
		};
	}

	async function save() {
		error = '';
		const payload = buildPayload();
		if (!payload.language_id) return (error = '請選擇語言');
		if (!payload.difficulty_id) return (error = '請選擇難度');
		if (!payload.publish_date) return (error = '請選擇發布日期');
		if (payload.grid_data.cells.length === 0) return (error = '請至少填入一格答案');

		saving = true;
		try {
			if (isEdit) await api.put(`/admin/crossword/${puzzleId}`, payload);
			else await api.post('/admin/crossword', payload);
			goto('/admin/crossword');
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
				const p = await api.get<{
					language_id: number;
					difficulty_id: number;
					publish_date: string;
					status: 'draft' | 'scheduled' | 'published';
					grid_data: { rows: number; cols: number; cells: { r: number; c: number; answer: string }[] };
					clues: { across: Slot[]; down: Slot[] };
				}>(`/admin/crossword/${puzzleId}`);
				rows = p.grid_data.rows;
				cols = p.grid_data.cols;
				grid = makeGrid(rows, cols);
				for (const cell of p.grid_data.cells) grid[cell.r][cell.c] = cell.answer;
				grid = grid;
				publishDate = p.publish_date;
				status = p.status;
				for (const s of p.clues.across ?? []) clueText[`a-${s.number}`] = (s as unknown as { clue: string }).clue ?? '';
				for (const s of p.clues.down ?? []) clueText[`d-${s.number}`] = (s as unknown as { clue: string }).clue ?? '';
				languageCode = languages.find((l) => l.id === p.language_id)?.code ?? '';
				await loadLevels(languageCode);
				difficultyId = p.difficulty_id;
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
	<div class="builder">
		{#if error}<p class="error">{error}</p>{/if}

		<div class="row">
			<label>
				語言
				<select bind:value={languageCode} on:change={onLanguageChange} disabled={isEdit}>
					<option value="" disabled>選擇</option>
					{#each languages as lang (lang.id)}<option value={lang.code}>{lang.name_zh}</option>{/each}
				</select>
			</label>
			<label>
				難度
				<select bind:value={difficultyId} disabled={!languageCode}>
					<option value={null} disabled>選擇</option>
					{#each levels as level (level.id)}<option value={level.id}>{level.label_zh}</option>{/each}
				</select>
			</label>
			<label>
				發布日期
				<input type="date" bind:value={publishDate} />
			</label>
			<label>
				狀態
				<select bind:value={status}>
					<option value="draft">草稿</option>
					<option value="scheduled">已排程</option>
					<option value="published">發布</option>
				</select>
			</label>
		</div>

		<div class="size">
			<label>列 <input type="number" min="1" max="12" bind:value={rows} on:change={resize} /></label>
			<label>行 <input type="number" min="1" max="12" bind:value={cols} on:change={resize} /></label>
			<span class="hint">在格子輸入字母＝可填格；留空＝黑格（不可填）。編號會自動產生。</span>
		</div>

		<div class="grid" style={`grid-template-columns: repeat(${cols}, 2.6rem);`}>
			{#each Array(rows) as _, r}
				{#each Array(cols) as _, c}
					<div class="cell" class:block={grid[r][c] === ''}>
						{#if numbering.numberAt[`${r},${c}`]}
							<span class="num">{numbering.numberAt[`${r},${c}`]}</span>
						{/if}
						<input maxlength="1" value={grid[r][c]} on:input={(e) => onCell(r, c, e)} />
					</div>
				{/each}
			{/each}
		</div>

		<div class="clues">
			<div class="clue-col">
				<h3>橫向提示</h3>
				{#if numbering.across.length === 0}<p class="muted small">尚無橫向單字</p>{/if}
				{#each numbering.across as slot (slot.number)}
					<label class="clue-row">
						<span class="cno">{slot.number}. （{slot.length}字）</span>
						<input bind:value={clueText[`a-${slot.number}`]} placeholder="提示文字" />
					</label>
				{/each}
			</div>
			<div class="clue-col">
				<h3>縱向提示</h3>
				{#if numbering.down.length === 0}<p class="muted small">尚無縱向單字</p>{/if}
				{#each numbering.down as slot (slot.number)}
					<label class="clue-row">
						<span class="cno">{slot.number}. （{slot.length}字）</span>
						<input bind:value={clueText[`d-${slot.number}`]} placeholder="提示文字" />
					</label>
				{/each}
			</div>
		</div>

		<div class="actions">
			<button class="btn-primary" on:click={save} disabled={saving}>
				{saving ? '儲存中…' : isEdit ? '更新題目' : '建立題目'}
			</button>
			<a href="/admin/crossword" class="btn-cancel">取消</a>
		</div>
	</div>
{/if}

<style>
	.builder {
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
		min-width: 130px;
	}

	label {
		display: block;
		font-size: 0.9rem;
		color: #374151;
	}

	select,
	input {
		display: block;
		width: 100%;
		padding: 0.5rem;
		margin-top: 0.3rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 0.95rem;
		box-sizing: border-box;
		font-family: inherit;
	}

	select:disabled {
		background: #f3f4f6;
	}

	.size {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}
	.size label {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}
	.size input {
		width: 4rem;
		margin-top: 0;
	}
	.hint {
		font-size: 0.8rem;
		color: #9ca3af;
	}

	.grid {
		display: grid;
		gap: 3px;
		background: #111;
		padding: 3px;
		border-radius: 8px;
		width: fit-content;
	}

	.cell {
		position: relative;
		width: 2.6rem;
		height: 2.6rem;
		background: white;
	}
	.cell.block {
		background: #1f2937;
	}

	.num {
		position: absolute;
		top: 1px;
		left: 2px;
		font-size: 0.55rem;
		color: #6b7280;
		pointer-events: none;
		z-index: 1;
	}

	.cell input {
		width: 100%;
		height: 100%;
		border: none;
		text-align: center;
		font-size: 1.1rem;
		font-weight: 700;
		text-transform: uppercase;
		background: transparent;
		margin: 0;
		padding: 0;
		border-radius: 0;
	}
	.cell.block input {
		color: white;
	}
	.cell input:focus {
		outline: 2px solid #2563eb;
		outline-offset: -2px;
	}

	.clues {
		display: flex;
		gap: 2rem;
		flex-wrap: wrap;
	}
	.clue-col {
		flex: 1;
		min-width: 240px;
	}
	.clue-col h3 {
		font-size: 1rem;
		color: #111;
		border-bottom: 2px solid #111;
		padding-bottom: 0.3rem;
		margin-bottom: 0.6rem;
	}
	.clue-row {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		margin-bottom: 0.5rem;
	}
	.cno {
		width: 5rem;
		font-size: 0.85rem;
		color: #6b7280;
		white-space: nowrap;
	}
	.clue-row input {
		margin-top: 0;
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
	.small {
		font-size: 0.85rem;
	}
	.error {
		color: #dc2626;
		background: #fef2f2;
		padding: 0.6rem 1rem;
		border-radius: 8px;
	}
</style>
