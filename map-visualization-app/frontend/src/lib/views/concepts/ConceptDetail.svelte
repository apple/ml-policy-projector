<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import type { Concept } from '$lib/types';
	import { appClient, conceptList, currentDataset } from '$lib/store';
	import { conceptMetadataSave } from '$lib/api';
	import { Listgroup, Star } from 'flowbite-svelte';
	import { ArrowLeftOutline } from 'flowbite-svelte-icons';
	import { getRowsByExampleIds } from '$lib/mosaic/appQueries';

	export let focusedConcepts: Concept[];

	$: conceptStarFills = focusedConcepts.map((c) => getFill(c));

	const getFill = (c: Concept) => (c.starred ? 100 : 0);

	function filterConcepts(concepts: Concept[]) {
		let names = focusedConcepts.map((c) => c.name);
		return sortConcepts(concepts).filter((c) => (c.count ?? 0 > 0) && names.indexOf(c.name) < 0);
	}

	function sortConcepts(concepts: Concept[]): Concept[] {
		return concepts.sort((a, b) => {
			return b.count ?? 0 - (a.count ?? 0);
		});
	}

	function selectConcept(concept: Concept) {
		$appClient.filterByConcept(concept);
	}

	const cancelFilter = () => {
		$appClient.removeAllFilters();
	};

	async function getData(concept: Concept) {
		const exampleRows = await getRowsByExampleIds(concept.examples);
		const data = exampleRows.map((e: string[]) => e[2]);
		return data;
	}

	async function handleStar(concept: Concept, i: number) {
		concept.starred = !concept.starred;
		conceptStarFills[i] = getFill(concept);
		let message = await conceptMetadataSave($currentDataset, concept);
	}
</script>

<section class="flex flex-col justify-between h-full">
	<!-- Back button -->
	<div>
		<button onclick={cancelFilter} type="button" class="" aria-label="Remove">
			<div class="flex flex-row space-x-1 items-center">
				<ArrowLeftOutline class="h-5 w-5 text-gray-400" />
				<span class="text-xs text-gray-400 font-semibold">Back to all concepts</span>
			</div>
		</button>
	</div>

	{#each focusedConcepts as concept, i}
		<div class="mb-6">
			<p class="uppercase">Concept</p>
			<div class="flex flex-row justify-between items-center">
				<p class="text-sm font-semibold">{concept.display_name}</p>
				<Star
					size={20}
					onclick={() => handleStar(concept, i)}
					class="hover:cursor-pointer hover:opacity-75"
					fillPercent={conceptStarFills[i]}
					fillColor={'#eb4f27'}
					strokeColor={'#222'}
				/>
			</div>

			<div class="mt-4">
				<h4 class="text-xs uppercase">Definition</h4>
				{#if concept.definition}
					<p class="text-xs">{concept.definition}</p>
				{:else}
					<p class="text-xs text-gray-400">No definition available</p>
				{/if}
			</div>

			<div class="mt-4">
				<h4 class="text-xs uppercase">Example Model Outputs</h4>
				{#if concept.examples.length > 0}
					{#await getData(concept)}
						<p>Loading...</p>
					{:then data}
						<Listgroup class="w-full bg-transparent max-h-52 overflow-y-scroll">
							{#each data as item}
								<p class="py-2 px-3 text-xs">{item}</p>
							{/each}
						</Listgroup>
					{:catch error}
						<p class="text-xs text-gray-400">Error: {error.message}</p>
					{/await}
				{:else}
					<p class="text-xs text-gray-400">No examples available</p>
				{/if}
			</div>
		</div>
	{/each}

	<!-- Overlapping Concepts -->
	<div class="mt-10">
		{#if $conceptList}
			<p class="uppercase">Overlapping Concepts</p>
			{#each $conceptList as group}
				{@const groupConcepts = filterConcepts(group.concepts)}
				<h4>{group.name} ({groupConcepts?.length ?? 0})</h4>
				<div>
					{#each groupConcepts as concept}
						<button
							class="conceptRow pl-2 pb-1 whitespace-nowrap cursor-default text-slate-600 hover:text-accent"
							onclick={() => selectConcept(concept)}
						>
							<span class="conceptRowName text-sm">{concept.display_name ?? concept.name}</span>
							{#if concept.count !== undefined}
								<span class="text-xs font-semibold">({concept.count})</span>
							{/if}
						</button>
					{/each}
				</div>
			{/each}
		{/if}
	</div>
</section>
