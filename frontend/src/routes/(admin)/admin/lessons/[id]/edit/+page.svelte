<script lang="ts">
	import { page } from '$app/stores';
	import LessonForm from '$lib/components/LessonForm.svelte';

	$: lessonId = $page.params.id ?? '';
</script>

<svelte:head>
	<title>編輯課程 — Heniiii 後台</title>
</svelte:head>

<section class="admin">
	<a class="back" href="/admin/lessons">← 返回課程管理</a>
	<h1>編輯課程</h1>
	{#key lessonId}
		<LessonForm {lessonId} />
	{/key}
</section>

<style>
	.admin {
		max-width: 720px;
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
