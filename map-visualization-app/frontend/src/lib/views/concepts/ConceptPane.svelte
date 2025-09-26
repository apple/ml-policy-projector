<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { activeFilters } from '$lib/store';
	import type { Filter } from '$lib/types';
	import { isConceptFilter } from '$lib/types';
	import ConceptList from './ConceptList.svelte';
	import ConceptDetail from './ConceptDetail.svelte';
	import type { Concept } from '$lib/types';

	let focusedConcepts: Concept[];

	// Page state
	$: focusedConcepts = $activeFilters
		.filter((f: Filter) => isConceptFilter(f))
		.map((f) => f.concept);
</script>

{#if focusedConcepts.length == 0}
	<ConceptList />
{:else}
	<ConceptDetail {focusedConcepts} />
{/if}
