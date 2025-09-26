<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { leftSidebarOpen, rightSidebarOpen, pointCount, mapReady, currentDataset, bottomTrayHeight } from '$lib/store';
	import { bottomDrawerClosedHeight } from '$lib/constants';
	import FilterBreadcrumb from './FilterBreadcrumb.svelte';
	import LayerOptions from './LayerOptions.svelte';
	import ReprojectButton from './ReprojectButton.svelte';
	import LatentConceptsButton from './LatentConceptsButton.svelte';	
	import { Spinner} from 'flowbite-svelte';

	$: isLoading = ($mapReady == false) && ($currentDataset != undefined)
	$: isLoaded = ($mapReady) && ($currentDataset != undefined)
</script>

<div
	class="absolute z-40 top-0 left-0 pointer-events-none py-2 w-full max-w-full h-full flex flex-col justify-between"
	class:leftSidebar={$leftSidebarOpen}
	class:rightSidebar={$rightSidebarOpen}
>	
	{#if isLoaded}
	<!-- Top UI Area -->
	<div class="flex flex-row w-full justify-between px-12">
		<FilterBreadcrumb />
		<div class="flex flex-row space-x-2">
			<ReprojectButton />
			<LatentConceptsButton />
		</div>
	</div>
	<!-- Bottom UI Area -->
	<div class="absolute px-2 my-3 self-end flex flex-row items-end gap-2" style="bottom: {$bottomTrayHeight - bottomDrawerClosedHeight}px; right:0">
		<span class="text-sm text-secondary text-nowrap">{$pointCount} Cases</span>
		<LayerOptions />
	</div>
	{/if}

	<!-- Loading spinner -->
	{#if isLoading}
		<div class="max-w-full h-screen items-center flex flex-col justify-center">
			<Spinner color="gray" size="6" />
		</div>
	{/if}
</div>

<style>
	.leftSidebar {
		padding-left: calc(var(--sidebar-content-width));
	}

	.rightSidebar {
		padding-right: calc(var(--sidebar-content-width));
	}
</style>
