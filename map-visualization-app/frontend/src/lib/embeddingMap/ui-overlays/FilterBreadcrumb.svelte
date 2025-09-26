<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { GradientButton } from 'flowbite-svelte';
	import { activeFilters, appClient } from '$lib/store';
	import CloseOutline from 'flowbite-svelte-icons/CloseOutline.svelte';
	import type { Filter } from '$lib/types';

	const cancelFilter = (filter: Filter) => {
		console.log('Close filter', filter);
		$appClient.removeFilter(filter);
	};
</script>

<section class="pointer-events-auto flex-wrap flex flex-row gap-1">
	{#each $activeFilters as filter}
		<GradientButton size="xs" outline color="pinkToOrange" class="max-h-10">
			<span class="pr-1">{filter.display_name}</span>
			<span onclick={() => cancelFilter(filter)} role="button" tabindex="0" onkeydown={() => cancelFilter(filter)}>
				<CloseOutline
					title={{ id: 'my-title', title: 'Close Icon' }}
					desc={{ id: 'my-descrip', desc: 'X icon to close filter' }}
					ariaLabel="close icon"
				/>
			</span>
		</GradientButton>
	{/each}
</section>
