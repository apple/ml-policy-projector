<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import {
		Button,
		Spinner,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Range
	} from 'flowbite-svelte';
	import {
		CogOutline,
		MinusOutline,
		PlusOutline,
		PenOutline,
		QuestionCircleOutline,
		CheckCircleOutline
	} from 'flowbite-svelte-icons';
	import { currentDataset } from '$lib/store';
	import { type Policy } from '$lib/types';
	import { policyFindMatches } from '$lib/api';
	import { getRowsByConcepts, getRowsByExampleIds } from '$lib/mosaic/appQueries';

	export let selectedPolicy: Policy;

	// Policy selection
	let allExampleIDs: string[];
	let lastPolicyName: string;
	let candTableData: string[][];
	let isLoadingCands = false;
	let headerRow = ['ID', 'Input', 'Output', 'Policy', ''];
	let idIndex = 0; // Index of ID column in tables
	let caseCount = 50;

	$: selectedPolicy, clearCandTable(); // Clear candidate table on change

	function clearCandTable() {
		if (selectedPolicy.name != lastPolicyName) {
			candTableData = [];
			lastPolicyName = selectedPolicy.name;
		}
	}

	function handleRemoveExample(row: string[]) {
		let exIDToRemove = row[idIndex];
		// Remove from examples
		selectedPolicy.examples = selectedPolicy.examples.filter((ex_id) => ex_id != exIDToRemove);
	}

	function handleAddExample(row: string[]) {
		let exIDToAdd = row[idIndex];
		// Don't add if already present
		if (selectedPolicy.examples.includes(exIDToAdd)) return;
		// Add to examples
		selectedPolicy.examples = [exIDToAdd, ...selectedPolicy.examples];
		// Remove from set of candidates
		candTableData = candTableData.filter((row: string[]) => row[idIndex] != exIDToAdd);
	}

	function handleAddAllExamples() {
		// Add all candidates
		let candExIdsToAdd = candTableData.map((row: string[]) => row[idIndex]);
		selectedPolicy.examples = [...candExIdsToAdd, ...selectedPolicy.examples];
		// Remove candidates from their table
		candTableData = []; // Empty table
	}

	async function getData(conceptNames: string[], examples: string[]) {
		if (conceptNames != undefined) {
			let res;
			let rows;
			if (examples.length > 0) {
				// Get matches from saved examples
				res = await getRowsByExampleIds(examples);
				rows = res.map((row: string[]) => row.slice(0, 3));
			} else {
				// Get matches based on existing concept matching conditions
				res = await getRowsByConcepts(conceptNames);
				rows = res.rows.map((row: string[]) => row.slice(0, 3));
				// Add to examples
				let exIdsToAdd = rows.map((row: string[]) => row[idIndex]);
				selectedPolicy.examples = [...exIdsToAdd, ...selectedPolicy.examples];
			}
			let rowsActions = rows.map((r: string[]) => {
				let curAction = `${selectedPolicy.then.action} ${selectedPolicy.then.concept}`;
				r.push(curAction);
				return r;
			});
			return rowsActions;
		}
	}

	async function handleFindMatches() {
		candTableData = [];
		isLoadingCands = true;
		allExampleIDs = await policyFindMatches($currentDataset, selectedPolicy, caseCount);
		const exampleRows = await getRowsByExampleIds(allExampleIDs);
		let exampleRowsActions = exampleRows.map((r: string[]) => {
			let curAction = `${selectedPolicy.then.action} ${selectedPolicy.then.concept}`;
			r.push(curAction);
			return r;
		});
		candTableData = exampleRowsActions;
		isLoadingCands = false;
		return candTableData;
	}
</script>

<div class="">
	<div class="flex flex-row justify-between pr-2">
		<div class="mb-2">
			<h4 class="text-xs uppercase my-1">
				<div class="flex flex-row space-x-1 items-center">
					<CogOutline class="w-3 h-3" /> <span>Test Policy</span>
				</div>
			</h4>
			<div class="flex flex-row space-x-10">
				<div class="flex flex-row space-x-3">
					<Button color="blue" size="xs" onclick={handleFindMatches}>Find policy matches</Button>
					<div class="w-40">
						<span class="text-xs">Cases to review: {caseCount}</span>
						<Range id="range-minmax" min="0" max="400" step="10" size="sm" bind:value={caseCount} />
					</div>
				</div>
				<div class="flex flex-row space-x-3">
					<Button color="blue" size="xs" disabled>Execute policy actions</Button>
					<div class="w-40">
						<span class="text-xs">Cases to generate: 5</span>
						<Range id="range-minmax" min="0" max="20" step="1" size="sm" value={5} disabled />
					</div>
				</div>
			</div>
		</div>

		{#if candTableData.length > 0}
			<div class="mb-2">
				<h4 class="text-xs uppercase my-1">
					<div class="flex flex-row space-x-1 items-center">
						<PenOutline class="w-3 h-3" /> <span>Actions</span>
					</div>
				</h4>
				<div class="flex flex-row space-x-3">
					<Button color="light" size="xs" onclick={handleAddAllExamples}>Add all</Button>
					<Button color="light" size="xs" onclick={() => (candTableData = [])}>Clear</Button>
				</div>
			</div>
		{/if}
	</div>

	{#if selectedPolicy}
		<div class="">
			{#if isLoadingCands}
				<Spinner size="4" class="my-4" />
			{:else if candTableData.length > 0}
				<div class="">
					<h4 class="text-xs uppercase mt-4">
						<div class="flex flex-row space-x-1 items-center">
							<QuestionCircleOutline class="w-3 h-3" />
							<span>Policy Match Candidates ({candTableData.length})</span>
						</div>
					</h4>
					<div class="mt-1 max-h-52 tableWrapper border border-gray-200 rounded-md">
						<Table hoverable={true} class="w-full" color="blue">
							<TableHead class="border-b sticky top-0">
								{#each headerRow as h}
									<TableHeadCell class="tableCellHeader">{h}</TableHeadCell>
								{/each}
							</TableHead>
							<TableBody class="h-72 overflow-y-auto">
								{#each candTableData.length ? candTableData : [['', '', '', '', '']] as row}
									<TableBodyRow class="">
										{#each row as item}
											<TableBodyCell class="tableCell"
												><div class="tableCellContent">{item}</div></TableBodyCell
											>
										{/each}
										<TableBodyCell>
											<Button
												onclick={() => handleAddExample(row)}
												pill={true}
												color="alternative"
												class="px-2 py-1 text-[10px] font-light"
											>
												<PlusOutline class="w-4 h-4 pr-2" /> Add
											</Button>
										</TableBodyCell>
									</TableBodyRow>
								{/each}
							</TableBody>
						</Table>
					</div>
				</div>
			{/if}
		</div>

		{#if selectedPolicy.if.length > 0}
			{#await getData(selectedPolicy.if, selectedPolicy.examples)}
				<p></p>
			{:then data}
				<h4 class="text-xs uppercase mt-4">
					<div class="flex flex-row space-x-1 items-center">
						<CheckCircleOutline class="w-3 h-3" />
						<span>Policy Examples ({data.length})</span>
					</div>
				</h4>
				<div class="mt-1 max-h-52 tableWrapper border border-gray-200 rounded-md">
					<Table hoverable={true} class="w-full">
						<TableHead class="border-b sticky top-0">
							{#each headerRow as h}
								<TableHeadCell class="tableCellHeader">{h}</TableHeadCell>
							{/each}
						</TableHead>
						<TableBody class="h-72 overflow-y-auto">
							{#each data || ['', '', '', ''] as row}
								<TableBodyRow class="">
									{#each row as item}
										<TableBodyCell class="tableCell"
											><div class="tableCellContent">{item}</div></TableBodyCell
										>
									{/each}
									<TableBodyCell>
										<Button
											onclick={() => handleRemoveExample(row)}
											pill={true}
											color="alternative"
											class="px-2 py-1 text-[10px] font-light"
										>
											<MinusOutline class="w-4 h-4 pr-2" />Remove
										</Button>
									</TableBodyCell>
								</TableBodyRow>
							{/each}
						</TableBody>
					</Table>
				</div>
			{:catch error}
				<p>Error: {error.message}</p>
			{/await}
		{/if}
	{/if}
</div>
