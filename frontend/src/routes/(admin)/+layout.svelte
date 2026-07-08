<script lang="ts">
	import { currentUser, isLoggedIn } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		if (!$isLoggedIn) {
			goto('/login');
			return;
		}
		if ($currentUser?.role !== 'admin' && $currentUser?.role !== 'editor') {
			goto('/');
		}
	});
</script>

{#if $isLoggedIn && ($currentUser?.role === 'admin' || $currentUser?.role === 'editor')}
	<slot />
{/if}
