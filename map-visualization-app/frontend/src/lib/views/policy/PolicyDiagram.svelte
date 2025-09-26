<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { PolicyAction, type Policy } from '$lib/types';
	import { getAcronym } from '$lib/api';

	export let policy: Policy;

	const radius = 12;
	const xGap = 20;
	const yGap = 4;

	function computeXOffset(index: number) {
		return radius * (index + 1) + (xGap + radius) * index + xGap / 2;
	}

	function computeWidth() {
		let count = policy.if.length - 1 + ((policy.then.action == PolicyAction.BLOCK || policy.then.action == PolicyAction.WARNING)? 1 : policy.then.concept.length);
		return computeXOffset(count) + radius + xGap;
	}

	function getSymbolForAction(action: PolicyAction) {
		switch (action) {
			case PolicyAction.ADD:
				return '➕';
			case PolicyAction.BLOCK:
				return '✖️';
			case PolicyAction.SUPPRESS:
				return '➖';
			case PolicyAction.WARNING:
				return '!';
		}
	}
</script>

<svg class="text-xs m-auto pt-2" width={computeWidth()}>
	<g>
		<!-- Draw each concept IF clause as a circle -->
		{#each policy.if as clause, index}
			{@const x = computeXOffset(index)}
			{#if index > 0}
				<text
					x={x - radius - xGap / 2}
					y={radius * 1.25}
					text-anchor="middle"
					dominant-baseline="middle">&</text
				>
			{/if}
			<circle cx={x} cy={radius} r={radius} fill={'#f22'} />
			<text {x} y={radius * 3 + yGap} fill={'#444'} text-anchor="middle">{getAcronym(clause)}</text
			>
		{/each}

		<!-- Draw arrow -->
		<text
			x={computeXOffset(policy.if.length) - radius - xGap / 2}
			y={radius * 1.25}
			text-anchor="middle"
			dominant-baseline="middle">→</text
		>

		<!-- Draw THEN clause symbol -->
		{#if policy.then.concept.length > 0}
			<!-- Multi-clause then -->
			{#each policy.then.concept as clause, index}
				{@const x = computeXOffset(policy.if.length + index)}
				<circle
					cx={x}
					cy={radius}
					r={radius}
					stroke={'#f22'}
					stroke-width={2}
					fill={'transparent'}
				/>
				<text
					class="action-icon"
					{x}
					y={radius * 1.25}
					dominant-baseline="middle"
					fill={'#444'}
					text-anchor="middle">{getSymbolForAction(policy.then.action)}</text
				>
				<text {x} y={radius * 3 + yGap} fill={'#444'} text-anchor="middle"
					>{getAcronym(clause)}</text
				>
			{/each}
		{:else}
			<!-- Single action then -->
			{@const thenX = computeXOffset(policy.if.length)}
			<circle
				cx={thenX}
				cy={radius}
				r={radius}
				stroke={'#f22'}
				stroke-width={2}
				fill={'transparent'}
			/>
			<text
				class="action-icon"
				x={thenX}
				y={radius * 1.25}
				dominant-baseline="middle"
				fill={'#444'}
				text-anchor="middle">{getSymbolForAction(policy.then.action)}</text
			>
			<text x={thenX} y={radius * 3 + yGap} fill={'#444'} text-anchor="middle"
				>{policy.then.action}</text
			>
		{/if}
	</g>
</svg>

<style>
	.action-icon {
		font-weight: bold;
	}
</style>
