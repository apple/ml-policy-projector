<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { currentDataset, activeFilters, pointCount } from '$lib/store';
	import { reproject } from '$lib/api';
	import ArrowsRepeatOutline from 'flowbite-svelte-icons/ArrowsRepeatOutline.svelte';
	import { Button } from 'flowbite-svelte';

	function triggerReproject() {
		reproject($currentDataset, $activeFilters);
	}
</script>

{#if $pointCount > 15}
	<div class="flex flex-col items-center w-12">
		<Button pill={true} outline={true} onclick={triggerReproject} class="!p-2 pointer-events-auto">
			<ArrowsRepeatOutline class="w-6 h-6" /></Button
		>
		<p class="text-[10px] text-center text-accent">Reproject</p>
	</div>
{/if}
