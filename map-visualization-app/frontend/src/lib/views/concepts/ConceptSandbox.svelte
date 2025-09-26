<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import {
		Select,
		Input,
		Textarea,
		Button,
		GradientButton,
		Spinner,
		Dropdown,
		Radio
	} from 'flowbite-svelte';
	import { ChevronDownOutline } from 'flowbite-svelte-icons';
	import { currentDataset, conceptList, activeFilters, bottomTrayHeight } from '$lib/store';
	import { type Concept, type ConceptGroup, AuthoringMode } from '$lib/types';
	import { conceptMetadataSave, getFocusedConcepts, conceptCreate } from '$lib/api';
	import { emptyConcept, bottomDrawerClosedHeight } from '$lib/constants';
	import ConceptSandboxActions from './ConceptSandboxActions.svelte';

	const DEBUG = false;

	let conceptOptions = getConceptOptions();
	let selectedConceptName: string = conceptOptions[0]?.value ?? '';
	let selectedConcept: Concept | undefined;
	let newConcept: Concept = structuredClone(emptyConcept);
	let isSaving = false;
	let isEditing = false;
	let conceptAuthMode: string = AuthoringMode.EDIT;
	let conceptAuthModeOptions: string[] = Object.values(AuthoringMode);

	// Page state
	$: focusedConcept = getFocusedConcepts($activeFilters, $conceptList)[0]; // Get first focused concept
	$: if (focusedConcept) {
		selectedConceptName = focusedConcept.name;
	}
	$: selectedConcept = handleSelectedConcept(selectedConceptName);

	function handleSelectedConcept(selectedConceptName: string) {
		if (focusedConcept) {
			return focusedConcept;
		} else {
			let res = $conceptList
				.flatMap((conceptGroup: ConceptGroup) => {
					return conceptGroup.concepts.map((c) => c);
				})
				.find((c: Concept) => c.name == selectedConceptName);
			return res;
		}
	}

	function getConceptOptions() {
		let conceptArray = $conceptList.flatMap((conceptGroup: ConceptGroup) => {
			return conceptGroup.concepts.map((c) => ({ value: c.name, name: c.display_name ?? '' }));
		});
		return conceptArray;
	}

	async function handleMetadataChange() {
		isSaving = true;
		if (selectedConcept) {
			let message = await conceptMetadataSave($currentDataset, selectedConcept);
			if (DEBUG) console.log(message);
		}
		isSaving = false;
	}

	async function handleCreateConcept() {
		isSaving = true;
		newConcept.name = newConcept.display_name ?? '';
		let message = await conceptCreate($currentDataset, newConcept);
		if (DEBUG) console.log(message);
		isSaving = false;
		newConcept = structuredClone(emptyConcept); // Refresh concept to empty state
	}
</script>

<section
	class="overflow-y-scroll"
	style="max-height: calc({$bottomTrayHeight - bottomDrawerClosedHeight}px)"
>
	{#if selectedConcept}
		<div class="flex flex-row w-full justify-between p-4">
			<div class="w-1/3 pr-6">
				<h4 class="text-xs uppercase mt-1">Concept</h4>
				<div class="flex">
					<button
						id="mode-button"
						class="w-24 shrink-0 z-10 inline-flex items-center py-2.5 px-4 text-sm font-medium text-center text-gray-500 bg-gray-100 border border-gray-300 rounded-s-lg hover:bg-gray-200 focus:ring-4 focus:outline-none focus:ring-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600 dark:focus:ring-gray-700 dark:text-white dark:border-gray-600"
						type="button"
					>
						{conceptAuthMode}
						<ChevronDownOutline class="w-6 h-6 ms-2" />
					</button>
					<Dropdown class="w-24 p-3 space-y-3 text-sm">
						{#each conceptAuthModeOptions as opt}
							<li>
								<Radio name="group1" bind:group={conceptAuthMode} value={opt}>{opt}</Radio>
							</li>
						{/each}
					</Dropdown>
					{#if conceptAuthMode == AuthoringMode.EDIT}
						<Select
							items={conceptOptions}
							bind:value={selectedConceptName}
							class="!rounded-s-none"
							size="sm"
							placeholder={'Select concept...'}
							disabled={focusedConcept != undefined}
						/>
					{:else if conceptAuthMode == AuthoringMode.CREATE}
						<Input
							type="text"
							bind:value={newConcept.display_name}
							placeholder={'Enter concept name'}
							class="!rounded-s-none"
							onfocus={() => (isEditing = true)}
							onblur={() => (isEditing = false)}
						/>
					{/if}
				</div>

				{#if conceptAuthMode == AuthoringMode.EDIT}
					<div class="mb-2">
						<h4 class="text-xs uppercase mt-1">Definition</h4>
						<Textarea
							id="definition"
							bind:value={selectedConcept.definition}
							placeholder="Enter definition"
							onfocus={() => (isEditing = true)}
							onblur={() => (isEditing = false)}
							rows={5}
						/>
					</div>

					<div class="">
						<GradientButton
							size="xs"
							outline
							color="pinkToOrange"
							class="w-full"
							type="submit"
							onclick={handleMetadataChange}
						>
							Save Changes
							{#if isSaving}
								<Spinner class="ml-2" size="4" />
							{/if}
						</GradientButton>
					</div>
				{:else if conceptAuthMode == AuthoringMode.CREATE}
					<div class="mb-2">
						<h4 class="text-xs uppercase mt-1">Definition</h4>
						<Textarea
							id="definition"
							bind:value={newConcept.definition}
							placeholder="Enter definition (ex: Does the text... ?)"
							onfocus={() => (isEditing = true)}
							onblur={() => (isEditing = false)}
							rows={5}
						/>
					</div>

					<div class="">
						<Button
							size="xs"
							class="w-full"
							color="alternative"
							type="submit"
							onclick={handleCreateConcept}
						>
							Create concept
							{#if isSaving}
								<Spinner class="ml-2" size="4" />
							{/if}
						</Button>
					</div>
				{/if}
			</div>

			<div class="w-2/3">
				<!-- Hide sandbox actions when editing fields to avoid flickering -->
				<div class="fade" style:opacity={isEditing ? "0" : "1"}>
					{#if conceptAuthMode == AuthoringMode.EDIT}
						<ConceptSandboxActions bind:selectedConcept />
					{:else if conceptAuthMode == AuthoringMode.CREATE}
						<ConceptSandboxActions bind:selectedConcept={newConcept} />
					{/if}
				</div>
			</div>
		</div>
	{/if}
</section>
