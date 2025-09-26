<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { createClassComponent } from "svelte/legacy";
	import { EmbeddingViewMosaic } from 'embedding-atlas/svelte';
	import { customTheme, defaultPointColor } from './theme';
	import MapOverlay from './map-layers/MapOverlay.svelte';
	import Tooltip from './Tooltip.svelte';
	import type { OverlayProxy, DataPoint, ViewportState } from 'embedding-atlas';
	import {
		mapFilter,
		mapZoom,
		showTopicLabels,
		mapSelectedPoints,
		mapTable,
		mapSelectionClauses
	} from '$lib/store';
	import { inputCol, outputCol, idCol, harmCol } from '$lib/constants';
	import { onMount, mount, unmount } from 'svelte';
	import * as vg from '@uwdata/vgplot';
	import { getRowsByRangeSelection } from '$lib/mosaic/appQueries';
	import { type Selection as MosaicSelection } from '@uwdata/mosaic-core';

	const DEBUG = true;

	// export let tableName: string;
	// export let width: number;
	// export let height: number;
	let { tableName, width, height } = $props();

	// map selection
	let selection: DataPoint[] = $state([]);
	let rangeSelection: typeof MosaicSelection = $state(null);

	class CustomTooltip {
		private component: Tooltip;

		constructor(
			target: HTMLDivElement,
			props: { tooltip: DataPoint; inputField: string; harmField: string }
		) {
			this.component = createClassComponent({ component: Tooltip, target: target, props: props });
		}
		update(props: { tooltip: DataPoint }) {
			this.component.$set(props);
		}
		destroy() {
			this.component.$destroy();
		}
	}

	class CustomMapOverlay {
		private component: MapOverlay;

		constructor(
			target: HTMLDivElement,
			props: { proxy: OverlayProxy }
		) {
			this.component = createClassComponent({ component: MapOverlay, target: target, props: props });
		}
		update(props: { proxy: OverlayProxy }) {
			this.component.$set(props);
		}
		destroy() {
			this.component.$destroy();
		}
	}
	
	const onRangeSelection = async (selection: Selection) => {
		if (!selection) {
			// no selected points
			mapSelectedPoints.set([]);
			if (DEBUG) console.log('Selection cleared');
		} else {
			if (DEBUG) console.log('Selected range:', selection, rangeSelection);
			let rows = await getRowsByRangeSelection(rangeSelection, $mapTable);
			if (DEBUG) console.log('Rows selected', rows);
			mapSelectedPoints.set(rows);
		}
		mapSelectionClauses.set(rangeSelection.clauses?.active ?? []);
	};

	// Set up additional metadata columns for tooltip
	function getAdditionalFields() {
		let fields: any = {};
		let columns = [inputCol, idCol, harmCol];
		for (let c of columns) {
			fields[c] = c;
		}
		return fields;
	}

	onMount(() => {
		rangeSelection = vg.Selection.crossfilter();
		rangeSelection.addEventListener('value', onRangeSelection);
	});
</script>

<div class="funny" class:hideLabels={!$showTopicLabels}>
	<EmbeddingViewMosaic
		{width}
		{height}
		table={tableName}
		filter={$mapFilter}
		x="x"
		y="y"
		text={outputCol}
		identifier="rowID"
		theme={customTheme}
		categoryColors={defaultPointColor}
		{rangeSelection}
		automaticLabels={false}
		additionalFields={getAdditionalFields()}
		customTooltip={{
			class: CustomTooltip,
			props: {
				inputField: inputCol,
				harmField: harmCol
			}
		}}
		customOverlay={{ class: CustomMapOverlay, props: {} }}
		bind:tooltip={selection}
		onViewportState = { (viewportState: ViewportState) => 
			mapZoom.set(viewportState?.scale)
		}
	/>
</div>
