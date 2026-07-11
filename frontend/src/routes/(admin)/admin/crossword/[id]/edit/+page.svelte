<script lang="ts">
	import { page } from '$app/stores';
	import CrosswordBuilder from '$lib/components/CrosswordBuilder.svelte';

	$: puzzleId = $page.params.id ?? '';
</script>

<svelte:head>
	<title>編輯填字 — Heniiii 後台</title>
</svelte:head>

<section class="admin">
	<a class="back" href="/admin/crossword">← 填字管理</a>
	<h1>編輯填字題目</h1>
	{#key puzzleId}
		<CrosswordBuilder {puzzleId} />
	{/key}
</section>

<style>
	.admin {
		max-width: 820px;
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
</style>
