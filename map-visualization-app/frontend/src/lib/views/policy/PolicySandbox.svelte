<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import {
		Textarea,
		Button,
		GradientButton,
		Spinner,
		Select,
		MultiSelect,
		Dropdown,
		Radio,
		Input
	} from 'flowbite-svelte';
	import { ChevronDownOutline } from 'flowbite-svelte-icons';
	import {
		conceptList,
		policyList,
		currentDataset,
		activeFilters,
		bottomTrayHeight
	} from '$lib/store';
	import {
		type Policy,
		PolicyAction,
		AuthoringMode,
		type Concept,
		type ConceptGroup
	} from '$lib/types';
	import { policyMetadataSave, getFocusedPolicies, policyCreate } from '$lib/api';
	import { emptyPolicy, bottomDrawerClosedHeight } from '$lib/constants';
	import PolicySandboxActions from './PolicySandboxActions.svelte';

	// Policy selection
	let policyOptions = getPolicyOptions();
	let selectedPolicyName: string = policyOptions[0].name;
	let selectedPolicy: Policy | undefined;
	let newPolicy: Policy = structuredClone(emptyPolicy);
	let isSaving = false;
	let isEditing = false;
	let policyAuthMode: string = AuthoringMode.EDIT;
	let policyAuthModeOptions: string[] = Object.values(AuthoringMode);

	// If conditions
	let conceptOptions = getConceptOptions();

	// Then actions
	const actionOptions = Object.values(PolicyAction);
	let thenActionOptions = actionOptions.map((pa) => ({ value: pa, name: pa }));

	// Page state
	$: focusedPolicy = getFocusedPolicies($activeFilters)[0]; // Get first focused policy
	$: if (focusedPolicy) {
		selectedPolicyName = focusedPolicy.name;
	}
	$: selectedPolicy = handleSelectedPolicy(selectedPolicyName);

	function getPolicyOptions() {
		return $policyList.map((p: Policy) => ({ value: p.name, name: p.name }));
	}

	function getConceptOptions() {
		let conceptArray = $conceptList.flatMap((conceptGroup: ConceptGroup) => {
			return conceptGroup.concepts.map((c: Concept) => ({ value: c.name, name: c.name }));
		});
		return conceptArray;
	}

	function handleSelectedPolicy(selectedPolicyName: string) {
		if (focusedPolicy) {
			return focusedPolicy;
		} else {
			let res = $policyList.find((c: Policy) => c.name == selectedPolicyName);
			return res;
		}
	}

	async function handleMetadataChange() {
		if (selectedPolicy) {
			isSaving = true;
			let message = await policyMetadataSave($currentDataset, selectedPolicy);
			isSaving = false;
		}
	}

	async function handleCreatePolicy() {
		isSaving = true;
		let message = await policyCreate($currentDataset, newPolicy);
		isSaving = false;
		newPolicy = structuredClone(emptyPolicy); // Refresh concept to empty state
	}

	function handleThenActionChange(curPolicy: Policy) {
		if (
			curPolicy.then.action == PolicyAction.BLOCK ||
			curPolicy.then.action == PolicyAction.WARNING
		) {
			curPolicy.then.concept = []; // clear associated concept
		}
	}
</script>

<section
	class="overflow-y-scroll"
	style="max-height: calc({$bottomTrayHeight - bottomDrawerClosedHeight}px)"
>
	{#if selectedPolicy}
		<div class="flex flex-row w-full justify-between p-4">
			<div class="w-1/3 pr-6 overflow-y-scroll">
				<h4 class="text-xs uppercase mt-1">Policy</h4>
				<div class="flex">
					<button
						id="mode-button"
						class="w-24 shrink-0 z-10 inline-flex items-center py-2.5 px-4 text-sm font-medium text-center text-gray-500 bg-gray-100 border border-gray-300 rounded-s-lg hover:bg-gray-200 focus:ring-4 focus:outline-none focus:ring-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600 dark:focus:ring-gray-700 dark:text-white dark:border-gray-600"
						type="button"
					>
						{policyAuthMode}
						<ChevronDownOutline class="w-6 h-6 ms-2" />
					</button>
					<Dropdown class="w-24 p-3 space-y-3 text-sm">
						{#each policyAuthModeOptions as opt}
							<li>
								<Radio name="group1" bind:group={policyAuthMode} value={opt}>{opt}</Radio>
							</li>
						{/each}
					</Dropdown>
					{#if policyAuthMode == AuthoringMode.EDIT}
						<Select
							items={policyOptions}
							bind:value={selectedPolicyName}
							class="!rounded-s-none"
							size="sm"
							placeholder={'Select policy...'}
							disabled={focusedPolicy != undefined}
						/>
					{:else if policyAuthMode == AuthoringMode.CREATE}
						<Input
							type="text"
							bind:value={newPolicy.name}
							placeholder={'Enter policy name'}
							class="!rounded-s-none"
							onfocus={() => (isEditing = true)}
							onblur={() => (isEditing = false)}
						/>
					{/if}
				</div>

				{#if policyAuthMode == AuthoringMode.EDIT}
					<div class="mb-2">
						<h4 class="text-xs uppercase mt-1">Description</h4>
						<Textarea
							id="description"
							bind:value={selectedPolicy.description}
							placeholder="Enter description"
							onfocus={() => (isEditing = true)}
							onblur={() => (isEditing = false)}
							rows={4}
						/>
					</div>

					<div class="mb-4">
						<h4 class="text-xs uppercase mt-1">If</h4>
						<MultiSelect
							items={conceptOptions}
							value={selectedPolicy.if}
							size="sm"
							placeholder={'Select matching conditions...'}
						/>
					</div>

					<div class="mb-4">
						<h4 class="text-xs uppercase mt-1">Then</h4>
						<div class="mb-2 flex flex-row w-full space-x-2">
							<div class="w-1/3">
								<Select
									items={thenActionOptions}
									bind:value={selectedPolicy.then.action}
									size="sm"
									placeholder={'Select action...'}
									onchange={() => {
										if (selectedPolicy) {
											handleThenActionChange(selectedPolicy);
										}
									}}
								/>
							</div>
							{#if selectedPolicy.then.action == PolicyAction.ADD || selectedPolicy.then.action == PolicyAction.SUPPRESS}
								<div class="w-2/3">
									<MultiSelect
										items={conceptOptions}
										bind:value={selectedPolicy.then.concept}
										size="sm"
										placeholder={'Select concept...'}
									/>
								</div>
							{/if}
						</div>
					</div>

					<div class="mb-10">
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
				{:else if policyAuthMode == AuthoringMode.CREATE}
					<div class="mb-2">
						<h4 class="text-xs uppercase mt-1">Description</h4>
						<Textarea
							id="description"
							bind:value={newPolicy.description}
							placeholder="Enter description (ex: Avoid content that..., Only disallow content that... )"
							onfocus={() => (isEditing = true)}
							onblur={() => (isEditing = false)}
							rows={4}
						/>
					</div>

					<div class="mb-4">
						<h4 class="text-xs uppercase mt-1">If</h4>
						<MultiSelect
							items={conceptOptions}
							bind:value={newPolicy.if}
							size="sm"
							placeholder={'Select matching conditions...'}
						/>
					</div>

					<div class="mb-4">
						<h4 class="text-xs uppercase mt-1">Then</h4>
						<div class="mb-2 flex flex-row w-full space-x-2">
							<div class="w-1/3">
								<Select
									items={thenActionOptions}
									bind:value={newPolicy.then.action}
									size="sm"
									placeholder={'Select action...'}
									onchange={() => handleThenActionChange(newPolicy)}
								/>
							</div>
							{#if newPolicy.then.action == PolicyAction.ADD || newPolicy.then.action == PolicyAction.SUPPRESS}
								<div class="w-2/3">
									<MultiSelect
										items={conceptOptions}
										bind:value={newPolicy.then.concept}
										size="sm"
										placeholder={'Select concept...'}
									/>
								</div>
							{/if}
						</div>
					</div>

					<div class="mb-10">
						<Button
							size="xs"
							class="w-full"
							color="alternative"
							type="submit"
							onclick={handleCreatePolicy}
						>
							Save Changes
							{#if isSaving}
								<Spinner class="ml-2" size="4" />
							{/if}
						</Button>
					</div>
				{/if}
			</div>

			<div class="w-2/3">
				<!-- Hide sandbox actions when editing fields to avoid flickering -->
				<div class="fade" style:opacity={isEditing ? '0' : '1'}>
					{#if policyAuthMode == AuthoringMode.EDIT}
						<PolicySandboxActions bind:selectedPolicy />
					{:else if policyAuthMode == AuthoringMode.CREATE}
						<PolicySandboxActions bind:selectedPolicy={newPolicy} />
					{/if}
				</div>
			</div>
		</div>
	{/if}
</section>
