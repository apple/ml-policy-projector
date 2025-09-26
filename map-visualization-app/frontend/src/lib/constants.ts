/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { PolicyAction, type Concept, type Policy } from './types';

export const appName = '🌐 Policy Projector';

// SQL Tables
export const baseProjectionTableName = 'baseProjection';
export const categoricalTableName = 'tabularParquet';
export const featureTableName = 'conceptFeatures';

// SQL Views
export const baseTableView = 'baseTableView';
export const mainlandView = 'mainland';

// table defaults
export const paginationLimit = 100;

// Column names
export const inputCol = 'user_input';
export const outputCol = 'model_output';
export const idCol = 'id';
export const harmCol = 'input_harm_cat';

// Bottom Drawer Views
export enum DrawerView {
	AddConcept = 0,
	AddPolicy = 1,
	DataTable = 2,
	Collapse = 3
}

// Bottom Drawer Heights
export const bottomDrawerClosedHeight = 60;
export const bottomDrawerOpenHeight = 400;

// Concept Groups
export const latentConceptGroupName = 'Suggested Concepts';

// Empty Concept
export const emptyConcept: Concept = {
	name: '',
	display_name: '',
	definition: '',
	examples: [],
	starred: false,
	count: undefined,
	centroid: undefined
};

// Empty Policy
export const emptyPolicy: Policy = {
	name: '',
	id: '',
	index: undefined,
	description: '',
	if: [],
	then: { action: PolicyAction.NONE, concept: [] },
	examples: [],
	count: undefined,
	centroid: undefined
};
