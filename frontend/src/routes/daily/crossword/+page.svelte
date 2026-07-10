<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api/client';
	import { isLoggedIn } from '$lib/stores/auth';

	interface CellPlay {
		r: number;
		c: number;
		number?: number;
	}
	interface Clue {
		number: number;
		row: number;
		col: number;
		length: number;
		clue: string;
	}
	interface Puzzle {
		id: string;
		publish_date: string;
		rows: number;
		cols: number;
		cells: CellPlay[];
		clues: { across: Clue[]; down: Clue[] };
	}
	interface SubmitResult {
		score: number;
		base_score: number;
		time_bonus: number;
		correct_cells: number;
		total_cells: number;
		is_perfect: boolean;
		per_cell: Record<string, boolean>;
		solution: Record<string, string>;
	}

	let puzzle: Puzzle | null = null;
	let loading = true;
	let error = '';

	let answers: Record<string, string> = {};
	let playable = new Set<string>();
	let numberAt: Record<string, number> = {};

	let seconds = 0;
	let timer: ReturnType<typeof setInterval> | null = null;

	let submitting = false;
	let result: SubmitResult | null = null;

	const key = (r: number, c: number) => `${r},${c}`;

	function mmss(total: number): string {
		const m = Math.floor(total / 60)
			.toString()
			.padStart(2, '0');
		const s = (total % 60).toString().padStart(2, '0');
		return `${m}:${s}`;
	}

	function startTimer() {
		stopTimer();
		timer = setInterval(() => (seconds += 1), 1000);
	}
	function stopTimer() {
		if (timer) clearInterval(timer);
		timer = null;
	}

	async function focusCell(r: number, c: number) {
		await tick();
		const el = document.querySelector<HTMLInputElement>(`[data-key="${key(r, c)}"]`);
		el?.focus();
	}

	function onInput(r: number, c: number, e: Event) {
		if (result) return;
		const input = e.target as HTMLInputElement;
		const ch = input.value.slice(-1).toUpperCase();
		answers[key(r, c)] = ch;
		answers = answers;
		input.value = ch;
		if (ch) {
			// advance to the next playable cell in this row
			for (let cc = c + 1; cc < (puzzle?.cols ?? 0); cc++) {
				if (playable.has(key(r, cc))) return focusCell(r, cc);
			}
		}
	}

	function onKeydown(r: number, c: number, e: KeyboardEvent) {
		if (e.key === 'Backspace' && !answers[key(r, c)]) {
			for (let cc = c - 1; cc >= 0; cc--) {
				if (playable.has(key(r, cc))) {
					focusCell(r, cc);
					break;
				}
			}
		}
	}

	async function load() {
		loading = true;
		error = '';
		result = null;
		answers = {};
		seconds = 0;
		try {
			const date = $page.url.searchParams.get('date');
			puzzle = date
				? await api.get<Puzzle>(`/daily/crossword/${date}`)
				: (await api.get<{ puzzle: Puzzle | null }>('/daily/today')).puzzle;

			if (puzzle) {
				playable = new Set(puzzle.cells.map((c) => key(c.r, c.c)));
				numberAt = {};
				for (const cell of puzzle.cells) {
					if (cell.number) numberAt[key(cell.r, cell.c)] = cell.number;
				}
				startTimer();
			}
		} catch (err) {
			error = (err as { detail?: string })?.detail || '載入失敗';
		} finally {
			loading = false;
		}
	}

	async function submit() {
		if (!puzzle) return;
		submitting = true;
		error = '';
		try {
			result = await api.post<SubmitResult>('/daily/crossword/submit', {
				puzzle_id: puzzle.id,
				answers,
				time_spent_seconds: seconds
			});
			stopTimer();
		} catch (err) {
			error = (err as { detail?: string })?.detail || '提交失敗';
		} finally {
			submitting = false;
		}
	}

	onMount(load);
	onDestroy(stopTimer);
</script>

<svelte:head>
	<title>今日填字 — Heniiii</title>
</svelte:head>

<section class="crossword">
	<a class="back" href="/daily">← 每日挑戰</a>

	{#if !$isLoggedIn}
		<div class="gate">
			<h2>請先登入</h2>
			<p>登入後即可挑戰今日填字並記錄分數。</p>
			<a class="btn-primary" href="/login">前往登入</a>
		</div>
	{:else if loading}
		<p class="muted">載入中…</p>
	{:else if error && !puzzle}
		<p class="error">{error}</p>
	{:else if !puzzle}
		<p class="muted">今日尚無題目。</p>
	{:else}
		<header class="head">
			<h1>今日填字</h1>
			<div class="timer" class:stopped={!!result}>⏱ {mmss(seconds)}</div>
		</header>

		{#if result}
			<div class="result" class:perfect={result.is_perfect}>
				<div class="score">{result.score} 分</div>
				<div class="breakdown">
					基礎 {result.base_score} + 時間加成 {result.time_bonus}
					· 答對 {result.correct_cells}/{result.total_cells}
					{#if result.is_perfect}· 🎉 全對！{/if}
				</div>
			</div>
		{/if}

		<div class="board" style={`grid-template-columns: repeat(${puzzle.cols}, 2.6rem);`}>
			{#each Array(puzzle.rows) as _, r}
				{#each Array(puzzle.cols) as _, c}
					{#if playable.has(key(r, c))}
						<div
							class="cell"
							class:correct={result?.per_cell[key(r, c)] === true}
							class:wrong={result?.per_cell[key(r, c)] === false}
						>
							{#if numberAt[key(r, c)]}
								<span class="num">{numberAt[key(r, c)]}</span>
							{/if}
							<input
								data-key={key(r, c)}
								maxlength="1"
								value={result && result.per_cell[key(r, c)] === false
									? (result.solution[key(r, c)] ?? '')
									: (answers[key(r, c)] ?? '')}
								readonly={!!result}
								on:input={(e) => onInput(r, c, e)}
								on:keydown={(e) => onKeydown(r, c, e)}
							/>
						</div>
					{:else}
						<div class="cell block"></div>
					{/if}
				{/each}
			{/each}
		</div>

		<div class="clues">
			<div class="clue-col">
				<h3>橫向</h3>
				<ul>
					{#each puzzle.clues.across as clue (clue.number)}
						<li><b>{clue.number}.</b> {clue.clue}（{clue.length}）</li>
					{/each}
				</ul>
			</div>
			<div class="clue-col">
				<h3>縱向</h3>
				<ul>
					{#each puzzle.clues.down as clue (clue.number)}
						<li><b>{clue.number}.</b> {clue.clue}（{clue.length}）</li>
					{/each}
				</ul>
			</div>
		</div>

		{#if error}<p class="error">{error}</p>{/if}

		<div class="actions">
			{#if result}
				<button class="btn-secondary" on:click={load}>再玩一次</button>
			{:else}
				<button class="btn-primary" on:click={submit} disabled={submitting}>
					{submitting ? '提交中…' : '提交答案'}
				</button>
			{/if}
		</div>
	{/if}
</section>

<style>
	.crossword {
		max-width: 640px;
		margin: 0 auto;
	}

	.back {
		display: inline-block;
		margin-bottom: 1.5rem;
		color: #6b7280;
		text-decoration: none;
		font-size: 0.9rem;
	}
	.back:hover {
		color: #111;
	}

	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	.head h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
	}

	.timer {
		font-variant-numeric: tabular-nums;
		font-size: 1.2rem;
		font-weight: 600;
		color: #111;
		background: #f3f4f6;
		padding: 0.3rem 0.8rem;
		border-radius: 8px;
	}
	.timer.stopped {
		color: #9ca3af;
	}

	.board {
		display: grid;
		gap: 3px;
		background: #111;
		padding: 3px;
		border-radius: 8px;
		width: fit-content;
		margin-bottom: 2rem;
	}

	.cell {
		position: relative;
		width: 2.6rem;
		height: 2.6rem;
		background: white;
	}

	.cell.block {
		background: #111;
	}

	.num {
		position: absolute;
		top: 1px;
		left: 3px;
		font-size: 0.6rem;
		color: #6b7280;
		pointer-events: none;
	}

	.cell input {
		width: 100%;
		height: 100%;
		border: none;
		text-align: center;
		font-size: 1.2rem;
		font-weight: 700;
		text-transform: uppercase;
		background: transparent;
		color: #111;
		box-sizing: border-box;
		padding: 0;
	}

	.cell input:focus {
		outline: 2px solid #2563eb;
		outline-offset: -2px;
	}

	.cell.correct {
		background: #dcfce7;
	}
	.cell.wrong {
		background: #fee2e2;
	}
	.cell.wrong input {
		color: #dc2626;
	}

	.result {
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 1.2rem 1.5rem;
		margin-bottom: 1.5rem;
	}
	.result.perfect {
		border-color: #16a34a;
		background: #f0fdf4;
	}

	.score {
		font-size: 2rem;
		font-weight: 800;
		color: #111;
	}

	.breakdown {
		color: #6b7280;
		font-size: 0.9rem;
		margin-top: 0.3rem;
	}

	.clues {
		display: flex;
		gap: 2rem;
		margin-bottom: 2rem;
	}

	.clue-col {
		flex: 1;
	}

	.clue-col h3 {
		font-size: 1rem;
		color: #111;
		border-bottom: 2px solid #111;
		padding-bottom: 0.3rem;
		margin-bottom: 0.6rem;
	}

	.clue-col ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.clue-col li {
		font-size: 0.9rem;
		color: #374151;
	}

	.actions {
		margin-bottom: 3rem;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.8rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		display: inline-block;
	}
	.btn-primary:disabled {
		opacity: 0.5;
	}

	.btn-secondary {
		border: 1px solid #d1d5db;
		background: white;
		color: #374151;
		padding: 0.8rem 2rem;
		border-radius: 8px;
		font-size: 1rem;
		cursor: pointer;
	}

	.gate {
		text-align: center;
		padding: 4rem 1rem;
	}
	.gate h2 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}
	.gate p {
		color: #6b7280;
		margin-bottom: 1.5rem;
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
