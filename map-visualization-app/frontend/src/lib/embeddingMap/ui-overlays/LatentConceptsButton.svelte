<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { currentDataset, activeFilters } from '$lib/store';
	import { fetchLatentConcepts } from '$lib/api';
	import WandMagicSparklesOutline from 'flowbite-svelte-icons/WandMagicSparklesOutline.svelte';
	import { Button } from 'flowbite-svelte';

	function handleLatentConcepts() {
		fetchLatentConcepts($currentDataset, $activeFilters);
	}
</script>

<div>
	<div class="flex flex-col items-center w-12">
		<Button pill={true} outline={true} onclick={handleLatentConcepts} class="!p-2 pointer-events-auto">
			<WandMagicSparklesOutline class="w-6 h-6" /></Button
		>
		<p class="text-[10px] text-center text-accent">Suggest</p>
	</div>
</div>
