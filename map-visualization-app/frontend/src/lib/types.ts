/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

// Concepts
export type Concept = {
	name: string;
	display_name: string | undefined;
	definition: string;
	examples: string[];
	starred: boolean;
	count: number | undefined; // derived computed
	centroid: Position | undefined; // derived computed
};
export type ConceptGroup = {
	name: string;
	description: string;
	none: Concept;
	concepts: Concept[];
};

// Policy
export type Policy = {
	name: string;
	id: string;
	index: number | undefined;
	description: string;
	if: string[];
	then: { action: PolicyAction; concept: string[] };
	examples: string[];
	count: number | undefined; // derived computed
	centroid: Position | undefined; // derived computed
};
export enum PolicyAction {
	BLOCK = 'block',
	WARNING = 'warning',
	SUPPRESS = 'suppress',
	ADD = 'add',
	NONE = '' // an invalid policy action
}

// Authoring modes
export enum AuthoringMode {
	EDIT = 'Edit',
	CREATE = 'Create'
}

// Map display
export type Position = { x: number; y: number };

// Table display
export type ExampleRow = string[];

export type SQLSelectionClause = {
	source: any;
	value: any;
	predicate: any;
};

// Filters
export type Filter = { display_name: string };
export interface ConceptFilter extends Filter {
	concept: Concept;
}
export interface PolicyFilter extends Filter {
	policy: Policy;
}

// type helpers
export function isConceptFilter(f: Filter): f is ConceptFilter {
	return (f as ConceptFilter).concept !== undefined;
}
export function isPolicyFilter(f: Filter): f is PolicyFilter {
	return (f as PolicyFilter).policy !== undefined;
}
