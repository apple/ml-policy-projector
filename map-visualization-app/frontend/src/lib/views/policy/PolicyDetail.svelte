<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import type { Policy, PolicyAction } from '$lib/types';
	import { getAcronym } from '$lib/api';
	import { appClient } from '$lib/store';
	import { Listgroup } from 'flowbite-svelte';
	import PolicyDiagram from './PolicyDiagram.svelte';
	import { ArrowLeftOutline } from 'flowbite-svelte-icons';
	import { getRowsByConcepts, getRowsByExampleIds } from '$lib/mosaic/appQueries';

	export let focusedPolicies: Policy[];

	const cancelFilter = () => {
		$appClient.removeAllFilters();
	};

	function arrayToList(arr: string[]) {
		return arr.join(', ').replace(/, ((?:.(?!, ))+)$/, ' AND $1');
	}

	function parseThen(x: { action: PolicyAction; concept: string[] }) {
		// Fetch associated action and concepts to display their names
		if (x.concept.length > 0) {
			let conceptStr = arrayToList(x.concept);
			let conceptAcronym = getAcronym(conceptStr);
			return `${x.action.toUpperCase()} ${conceptAcronym}: ${conceptStr}`;
		} else {
			return `${x.action.toUpperCase()}`;
		}
	}

	async function getData(policy: Policy) {
		if (policy.if != undefined) {
			// Get matches based on existing concept matching conditions
			const resConcept = await getRowsByConcepts(policy.if);
			const conceptMatchRows = resConcept.rows.map((row: string[]) => row.slice(0, 3));
			// Get any additional examples saved to the policy
			const exampleRows = await getRowsByExampleIds(policy.examples);
			// totalCount = resConcept.count + exampleRows.length;
			let rows = exampleRows.concat(conceptMatchRows);
			const data = rows.map((e: string[]) => e[2]);
			return data;
		}
	}
</script>

<section class="flex flex-col justify-between h-full">
	<!-- Back button -->
	<div>
		<button onclick={cancelFilter} type="button" class="" aria-label="Remove">
			<div class="flex flex-row space-x-1 items-center">
				<ArrowLeftOutline class="h-5 w-5 text-gray-400" />
				<span class="text-xs text-gray-400 font-semibold">Back to all policies</span>
			</div>
		</button>
	</div>

	{#each focusedPolicies as policy}
		{@const hasValidSpec = policy.if.length > 0 && policy.then.action != ''}
		<p class="uppercase">Policy {(policy.index ?? 0) + 1}</p>
		<p class="text-sm font-semibold">{policy.name}</p>

		<div class="mt-4">
			<h4 class="text-xs uppercase mb-1">Description</h4>
			<p class="text-xs">{policy.description}</p>
		</div>

		<div class="mt-4">
			<h4 class="text-xs uppercase mb-1">Specification</h4>
			{#if hasValidSpec}
				<div class="bg-gray-100 rounded w-full h-14 mb-2">
					<PolicyDiagram {policy} />
				</div>
			{:else}
				<p class="text-xs text-gray-400">Specification not complete</p>
			{/if}

			<div class="mt-2 ml-4">
				<h4 class="text-xs uppercase mb-1">If:</h4>
				{#if policy.if.length > 0}
					<Listgroup class="w-full bg-transparent mb-4">
						{#each policy.if as ifCondition}
							<p class="py-2 px-3 text-xs">{getAcronym(ifCondition)}: {ifCondition}</p>
						{/each}
					</Listgroup>
				{:else}
					<p class="text-xs text-gray-400">No if-conditions</p>
				{/if}

				<h4 class="text-xs uppercase mb-1">Then:</h4>
				{#if policy.then.action != ''}
					<Listgroup class="w-full bg-transparent mb-4">
						<p class="py-2 px-3 text-xs">{parseThen(policy.then)}</p>
					</Listgroup>
				{:else}
					<p class="text-xs text-gray-400">No then-action</p>
				{/if}
			</div>
		</div>

		<div class="mt-4">
			<h4 class="text-xs uppercase">Example Model Outputs</h4>
			{#if hasValidSpec}
				{#await getData(policy)}
					<p>Loading...</p>
				{:then data}
					<Listgroup class="w-full bg-transparent max-h-52 overflow-y-scroll">
						{#each data as item}
							<p class="py-2 px-3 text-xs">{item}</p>
						{/each}
					</Listgroup>
				{:catch error}
					<p class="text-xs text-gray-400">No examples available</p>
				{/await}
			{:else}
				<p class="text-xs text-gray-400">Specification not complete</p>
			{/if}
		</div>
	{/each}
</section>
