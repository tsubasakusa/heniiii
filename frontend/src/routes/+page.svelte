<script lang="ts">
	import { isLoggedIn } from '$lib/stores/auth';
</script>

<svelte:head>
	<title>Heniiii — 語言學習平台</title>
</svelte:head>

<section class="hero">
	<h1>學英文、日文、台語</h1>
	<p>透過每日填字挑戰、單字卡和分級課程，讓語言學習成為日常習慣。</p>

	{#if !$isLoggedIn}
		<div class="cta">
			<a href="/register" class="btn-primary">免費開始</a>
			<a href="/daily" class="btn-secondary">先看看每日挑戰</a>
		</div>
	{:else}
		<div class="cta">
			<a href="/daily" class="btn-primary">今日挑戰</a>
			<a href="/flashcards" class="btn-secondary">複習單字卡</a>
		</div>
	{/if}
</section>

<style>
	.hero {
		text-align: center;
		padding: 6rem 2rem;
	}

	h1 {
		font-size: 3rem;
		font-weight: 800;
		margin-bottom: 1rem;
		color: #111;
	}

	p {
		font-size: 1.2rem;
		color: #6b7280;
		margin-bottom: 2rem;
	}

	.cta {
		display: flex;
		gap: 1rem;
		justify-content: center;
	}

	.btn-primary {
		background: #111;
		color: white;
		padding: 0.8rem 2rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
	}

	.btn-secondary {
		border: 1px solid #d1d5db;
		color: #374151;
		padding: 0.8rem 2rem;
		border-radius: 8px;
		text-decoration: none;
	}
</style>
