<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { activeFilters, appClient, policyList } from '$lib/store';
	import type { Policy, Filter } from '$lib/types';
	import { isPolicyFilter } from '$lib/types';
	import PolicyDetail from './PolicyDetail.svelte';

	let focusedPolicies: Policy[];

	// Page state
	$: focusedPolicies = $activeFilters.filter((f: Filter) => isPolicyFilter(f)).map((f) => f.policy);

	function selectPolicy(policy: Policy) {
		$appClient?.filterByPolicy(policy);
	}
</script>

{#if focusedPolicies.length > 0}
	<PolicyDetail {focusedPolicies} />
{:else}
	<section>
		<p class="text-xs text-gray-400 mb-2">Select a policy below to view details</p>
		{#if $policyList}
			{#each $policyList as policy}
				<ul class="text-sm mt-2">
					<li>
						<button
							class="policyRow pl-2 pb-1 whitespace-nowrap cursor-default text-slate-600 hover:text-accent"
							onclick={() => selectPolicy(policy)}
						>
							<span class="font-bold mr-2">P{(policy.index ?? 0) + 1}</span>
							<span class="policyRowName text-sm">
								{policy.name}
							</span>
							{#if policy.count !== undefined}
								<span class="text-xs font-semibold">({policy.count})</span>
							{/if}
						</button>
					</li>
				</ul>
			{/each}
		{/if}
	</section>
{/if}

<style>
	.policyRow {
		display: flex;
		justify-content: space-between;
		width: 100%;
	}
	.policyRowName {
		width: 100%;
		text-wrap: wrap;
		text-align: left;
	}
</style>
