<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import type { OverlayProxy } from 'embedding-atlas';
	import type { Concept } from '$lib/types';
	import { appClient } from '$lib/store';

	export let proxy: OverlayProxy;
	export let concept: Concept;

	async function selectConcept(ev: Event) {
		// prevent clicking points underneath
		ev.preventDefault();
		ev.stopPropagation();
		ev.stopImmediatePropagation();
		console.log(concept?.name + ' clicked!');

		// update filter
		$appClient.filterByConcept(concept);
	}
</script>

{#if concept.centroid && concept.count !== undefined && concept.count > 0}
	{@const loc = proxy.location(concept.centroid.x, concept.centroid.y)}
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<circle
		cx={loc.x}
		cy={loc.y}
		r={8}
		stroke={'#f22'}
		fill={'#eee'}
		onclick={(ev) => selectConcept(ev)}
		class="concept-point stroke-2 opacity-80 hover:opacity-100"
	/>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<text
		x={loc.x + 8}
		y={loc.y + 4}
		fill={'#444'}
		class="concept-point-label"
		onclick={(ev) => selectConcept(ev)}>{concept.display_name?.substring(0, 30)}</text
	>
{/if}

<style>
	.concept-point {
		cursor: pointer;
	}

	.concept-point-label {
		cursor: pointer;
		font-size: x-small;
		font-weight: 600;
		paint-order: stroke;
		stroke: #ffffffb0;
		stroke-width: 3px;
		stroke-linecap: butt;
		stroke-linejoin: miter;
	}
</style>
