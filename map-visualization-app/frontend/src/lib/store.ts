/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { type Writable, writable, type Readable, derived } from 'svelte/store';
import type { ConceptGroup, Filter, Policy, ExampleRow, SQLSelectionClause } from './types';
import {
	bottomDrawerClosedHeight,
	baseTableView,
	baseProjectionTableName,
	paginationLimit
} from './constants';
import { AppClient } from '$lib/mosaic/appClient';
import * as vg from '@uwdata/vgplot';
import { type Selection as MosaicSelection } from '@uwdata/mosaic-core';
import { get } from 'svelte/store';

// Concepts and Policies
export const appClient: Writable<AppClient> = writable();
export const activeFilters: Writable<Filter[]> = writable([]);
export const conceptList: Writable<ConceptGroup[]> = writable([]);
export const policyList: Writable<Policy[]> = writable([]);

// View panels
export const leftSidebarOpen = writable(true);
export const rightSidebarOpen = writable(false);
export const bottomTrayOpen = writable(false);
export const bottomTrayHeight = writable(bottomDrawerClosedHeight);
export const activeBottomSection = writable(0);

// Dataset loading
export const datasetOptions: Writable<string[]> = writable([]);
export const currentDataset: Writable<string> = writable();
export const pointCount: Writable<number> = writable(0);
export const mapReady: Writable<boolean> = writable(false);
export const mapTable: Writable<string> = writable(baseProjectionTableName);

// Embedding map view settings
export const showNone = writable(true);
export const mapZoom: Writable<number> = writable(1);
export const colorBy = writable('default');
export const autoReproject = writable(true);
export const showTopicLabels = writable(false);
export const showConceptMarkers = writable(true);
export const showLatentConceptMarkers = writable(false);
export const showPolicyMarkers = writable(false);
export const showOverlay = writable(true);

// Embedding map filters & selection
export const mapFilter: Writable<typeof MosaicSelection> = writable(vg.Selection.crossfilter());
export const mapSelectionClauses: Writable<SQLSelectionClause[]> = writable();
export const mapSelectedPoints: Writable<ExampleRow[]> = writable([]);

// Case table view
export const caseTableHeaders: Writable<string[]> = writable([]);
export const caseTableRows: Writable<ExampleRow[]> = writable([]);
export const caseTableSize: Readable<number> = derived(
	[caseTableRows, pointCount],
	([$caseTableRows, $pointCount]) => {
		if ($caseTableRows?.length >= paginationLimit) return $pointCount;
		return $caseTableRows.length;
	}
);

// Initializers
export function getOrInitializeClient(
	conceptList: ConceptGroup[],
	policyList: Policy[]
): AppClient {
	let existingClient = get(appClient);
	if (existingClient) {
		existingClient.conceptList = conceptList;
		existingClient.policyList = policyList;
		return existingClient;
	} else {
		let _mapFilter = get(mapFilter);
		// initialize client
		const client = new AppClient({
			filterBy: _mapFilter,
			as: _mapFilter,
			conceptList,
			policyList,
			projectionTable: baseTableView,
			showingNone: true
		});
		appClient.set(client);
		return client;
	}
}
