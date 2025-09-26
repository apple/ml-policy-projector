<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { showConceptMarkers, showLatentConceptMarkers, showPolicyMarkers, showTopicLabels, bottomTrayHeight } from '$lib/store';
	import { bottomDrawerClosedHeight } from '$lib/constants';
	import { Card, Toggle } from 'flowbite-svelte';
	import {
		ScaleBalancedSolid,
		LandmarkSolid,
		MapPinAltSolid,
		MapPinAltOutline,
		TextSizeOutline,
		LayersOutline
	} from 'flowbite-svelte-icons';
</script>

<Card class="!p-2 pointer-events-auto w-64">
	<Toggle
		size="small"
		class="bg-green rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
		bind:checked={$showPolicyMarkers}
	>
		<ScaleBalancedSolid /> <span class="ml-1">Policy</span>
	</Toggle>

	<Toggle
		size="small"
		class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
		bind:checked={$showConceptMarkers}
	>
		<MapPinAltSolid /> <span class="ml-1">Concepts</span>
	</Toggle>

	<Toggle 
		size="small" 
		class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
		bind:checked={$showLatentConceptMarkers}
	>
		<MapPinAltOutline /> <span class="ml-1">Suggested Concepts</span>
	</Toggle>

	<!-- <Toggle disabled size="small" class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600">
		<LandmarkSolid /> <span class="ml-1">Landmark Cases</span>
	</Toggle> -->

	<!-- <Toggle
		size="small"
		class="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-600"
		bind:checked={$showTopicLabels}
	>
		<TextSizeOutline /> <span class="ml-1">Topic Labels</span>
	</Toggle> -->

	<div class="text-secondary text-sm text-center" id="layerButton">
		<LayersOutline class="inline mr-1 align-text-bottom" /><span>Layers</span>
	</div>
</Card>
