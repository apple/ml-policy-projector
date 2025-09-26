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
		MinusOutline,
		PlusOutline,
		SearchOutline,
		PenOutline,
		QuestionCircleOutline,
		CheckCircleOutline
	} from 'flowbite-svelte-icons';
	import { currentDataset, appClient, mapSelectedPoints } from '$lib/store';
	import { getRowsByExampleIds } from '$lib/mosaic/appQueries';
	import { type Concept, type ExampleRow } from '$lib/types';
	import { conceptFindSimilar } from '$lib/api';

	export let selectedConcept: Concept;

	let allExampleIDs: string[];
	let lastConceptName: string;
	let candTableData: ExampleRow[];
	let isLoadingCands = false;
	let headerRow = ['ID', 'Input', 'Output', ''];
	let idIndex = 0; // Index of ID column in tables
	let totalCount = 0;
	let caseCount = 50;
	let mapSelectedCaseCount = 0;

	$: selectedConcept, clearCandTable(); // Clear candidate table on change
	$: mapSelectedCaseCount = $mapSelectedPoints?.length ?? 0;

	function clearCandTable() {
		if (selectedConcept.name != lastConceptName) {
			candTableData = [];
			lastConceptName = selectedConcept.name;
		}
	}

	function handleRemoveExample(row: ExampleRow) {
		let exIDToRemove = row[idIndex];
		// Remove from examples
		selectedConcept.examples = selectedConcept.examples.filter((ex_id) => ex_id != exIDToRemove);
	}

	function handleAddExample(row: ExampleRow) {
		let exIDToAdd = row[idIndex];
		// Don't add if already present
		if (selectedConcept.examples.includes(exIDToAdd)) return;
		// Add to examples
		selectedConcept.examples = [exIDToAdd, ...selectedConcept.examples];
		// Remove from set of candidates
		candTableData = candTableData.filter((row: ExampleRow) => row[idIndex] != exIDToAdd);
	}

	function handleAddAllExamples() {
		// Add all candidates
		let candExIdsToAdd = candTableData.map((row: ExampleRow) => row[idIndex]);
		selectedConcept.examples = [...candExIdsToAdd, ...selectedConcept.examples];
		// Remove candidates from their table
		candTableData = []; // Empty table
	}

	async function getData(examples: string[]) {
		if ($appClient != undefined && examples != undefined) {
			const exampleRows = await getRowsByExampleIds(examples);
			totalCount = exampleRows.length;
			return exampleRows;
		}
	}

	async function handleFindSimilar() {
		candTableData = [];
		isLoadingCands = true;
		allExampleIDs = await conceptFindSimilar($currentDataset, selectedConcept, caseCount);
		const exampleRows = await getRowsByExampleIds(allExampleIDs);
		candTableData = exampleRows;
		isLoadingCands = false;
		return candTableData;
	}

	async function handleAddMapSelection(rowList: ExampleRow[]) {
		isLoadingCands = true;
		candTableData = rowList;
		isLoadingCands = false;
		return candTableData;
	}
</script>

<section class="">
	<div class="flex flex-row justify-between pr-2">
		<div class="mb-2">
			<h4 class="text-xs uppercase my-1">
				<div class="flex flex-row space-x-1 items-center">
					<SearchOutline class="w-3 h-3" /> <span>Gather Examples</span>
				</div>
			</h4>
			<div class="flex flex-row space-x-10">
				<div class="flex flex-row space-x-3">
					<Button color="blue" size="xs" onclick={handleFindSimilar}>Find similar cases</Button>
					<div class="w-40">
						<span class="text-xs">Cases to review: {caseCount}</span>
						<Range id="range-minmax" min="0" max="400" step="10" size="sm" bind:value={caseCount} />
					</div>
					<!-- <Button color="blue" size="xs" disabled>Select from map</Button> -->
				</div>
				<div class="flex flex-row space-x-3">
					<Button color="blue" size="xs" disabled>Generate cases</Button>
					<div class="w-40">
						<span class="text-xs">Cases to generate: 5</span>
						<Range id="range-minmax" min="0" max="20" step="1" size="sm" value={5} disabled />
					</div>
				</div>
				{#if mapSelectedCaseCount}
					<div class="flex flex-row space-x-3">
						<Button
							color="blue"
							size="xs"
							onclick={() => handleAddMapSelection($mapSelectedPoints)}
							>Add {mapSelectedCaseCount} selected case{mapSelectedCaseCount > 1 ? 's' : ''}</Button
						>
					</div>
				{/if}
			</div>
		</div>

		{#if selectedConcept && candTableData.length}
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

	{#if selectedConcept && $appClient}
		<div class="">
			{#if isLoadingCands}
				<Spinner size="4" class="my-4" />
			{:else if candTableData.length}
				<div class="">
					<h4 class="text-xs uppercase mt-4">
						<div class="flex flex-row space-x-1 items-center">
							<QuestionCircleOutline class="w-3 h-3" />
							<span>Concept Candidates ({candTableData.length})</span>
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
								{#each candTableData.length ? candTableData : [['', '', '', '']] as row}
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

		{#if selectedConcept.examples.length > 0}
			{#await getData(selectedConcept.examples)}
				<p></p>
			{:then data}
				<h4 class="text-xs uppercase mt-4">
					<div class="flex flex-row space-x-1 items-center">
						<CheckCircleOutline class="w-3 h-3" />
						<span>Concept Examples ({totalCount})</span>
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
</section>
