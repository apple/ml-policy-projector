<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import type { OverlayProxy } from 'embedding-atlas';
	import {
		conceptList,
		showConceptMarkers,
		showLatentConceptMarkers,
		showPolicyMarkers,
		showOverlay,
		policyList
	} from '$lib/store';
	import { latentConceptGroupName } from '$lib/constants';
	import ConceptMarker from './ConceptMarker.svelte';
	import LatentConceptMarker from './LatentConceptMarker.svelte';
	import PolicyMarker from './PolicyMarker.svelte';

	export let proxy: OverlayProxy;
</script>

<svg width={proxy.width} height={proxy.height}>
	<g class="mapOverlay">
		{#if $showOverlay}
			<g visibility={$showConceptMarkers ? 'visible' : 'hidden'}>
				{#each $conceptList
					.filter((group) => group.name != latentConceptGroupName)
					.flatMap((group) => group.concepts) as item}
					<ConceptMarker concept={item} {proxy} />
				{/each}
			</g>

			<g visibility={$showPolicyMarkers ? 'visible' : 'hidden'}>
				{#each $policyList as item}
					<PolicyMarker policy={item} {proxy} />
				{/each}
			</g>

			<g visibility={$showLatentConceptMarkers ? 'visible' : 'hidden'}>
				{#each $conceptList
					.filter((group) => group.name == latentConceptGroupName)
					.flatMap((group) => group.concepts) as item}
					<LatentConceptMarker concept={item} {proxy} />
				{/each}
			</g>
		{/if}
	</g>
</svg>