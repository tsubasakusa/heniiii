<script lang="ts">
	import CrosswordBuilder from '$lib/components/CrosswordBuilder.svelte';
</script>

<svelte:head>
	<title>新增填字 — Heniiii 後台</title>
</svelte:head>

<section class="admin">
	<a class="back" href="/admin/crossword">← 填字管理</a>
	<h1>新增填字題目</h1>
	<CrosswordBuilder />
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
