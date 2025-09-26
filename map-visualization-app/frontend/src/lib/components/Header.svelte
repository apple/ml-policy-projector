<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { Navbar, NavBrand, Spinner } from 'flowbite-svelte';
	import Dropdown from './Dropdown.svelte';
	import { datasetOptions, currentDataset } from '$lib/store';
	import { refreshConceptsAndMap } from '$lib/api';
	import { page } from '$app/stores';

	export let title: String;

	const hasDataset = $page.url.searchParams.has('dataset');
	if (hasDataset) datasetOptions.set([$page.url.searchParams.get('dataset')!]);

	currentDataset.subscribe(async (value) => {
		if (value) {
			await refreshConceptsAndMap(value);
		}
	});
</script>

<Navbar fluid class="app-header border-b p-1">
	<NavBrand href="/">
		<h2 class="font-semibold px-2 pt-1">{title}</h2>
	</NavBrand>

	<div class="w-56 z-50">
		<Dropdown
			options={$datasetOptions}
			bind:selected={$currentDataset}
			placeholder={'Select dataset...'}
			title={'select dataset'}
			classNames={'text-xs'}
		/>
	</div>
</Navbar>
