<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { appClient, conceptList } from '$lib/store';
	import { type Concept } from '$lib/types';
	import { Star } from 'flowbite-svelte';

	const getFill = (c: Concept) => (c.starred ? 100 : 0);

	function sortConcepts(concepts: Concept[]): Concept[] {
		return concepts.sort((a, b) => {
			if (a.name > b.name) return 1;
			if (a.name < b.name) return -1;
			return 0;
		});
	}

	function selectConcept(concept: Concept) {
		$appClient.filterByConcept(concept);
	}
</script>

<section>
	<p class="text-xs text-gray-400 mb-2">Select a concept below to view details</p>
	{#if $conceptList}
		{#each $conceptList as group, group_i}
			<h4>{group.name} ({group.concepts?.length ?? 0})</h4>
			<div class="mt-2">
				{#each sortConcepts(group.concepts) as concept}
					<button
						class="conceptRow pl-2 pb-1 whitespace-nowrap cursor-default text-slate-600 hover:text-accent"
						onclick={() => selectConcept(concept)}
					>
						<span>
							<Star
								size={20}
								fillPercent={getFill(concept)}
								fillColor={'#eb4f27'}
								strokeColor={'none'}
							/>
						</span>
						<span class="conceptRowName text-sm">{concept.display_name ?? concept.name}</span>
						{#if concept.count !== undefined}
							<span class="text-xs font-semibold">({concept.count})</span>
						{/if}
					</button>
				{/each}
			</div>
		{/each}
	{/if}
</section>
