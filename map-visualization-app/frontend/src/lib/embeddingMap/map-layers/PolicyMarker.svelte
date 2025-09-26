<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import type { OverlayProxy } from 'embedding-atlas';
	import { type Policy, PolicyAction } from '$lib/types';
	import { appClient } from '$lib/store';

	export let proxy: OverlayProxy;
	export let policy: Policy;
	const radius = 8;

	function getSymbol() {
		switch (policy.then.action) {
			case PolicyAction.BLOCK:
				return 'x';
			case PolicyAction.WARNING:
				return '!';
			case PolicyAction.SUPPRESS:
				return '−';
			case PolicyAction.ADD:
				return '+';
			case PolicyAction.NONE:
				return '';
		}
	}

	async function selectPolicy(ev: Event) {
		// prevent clicking points underneath
		ev.preventDefault();
		ev.stopPropagation();
		ev.stopImmediatePropagation();
		console.log(policy?.name + ' clicked!');

		// update filter
		$appClient.filterByPolicy(policy);
	}
</script>

{#if policy.centroid && policy.count !== undefined && policy.count > 0}
	{@const loc = proxy.location(policy.centroid.x, policy.centroid.y)}
	{@const symbol = getSymbol()}
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<circle
		cx={loc.x}
		cy={loc.y}
		r={radius}
		stroke={'#f22'}
		fill={'#fff'}
		onclick={(ev) => selectPolicy(ev)}
		class="policy-point stroke-2 opacity-80 hover:opacity-100"
	/>
	<text
		class="policy-point-icon"
		fill={'#f22'}
		dominant-baseline="middle"
		text-anchor="middle"
		x={loc.x}
		y={loc.y}>{symbol}</text
	>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<text
		x={loc.x + 12}
		y={loc.y + 4}
		fill={'#444'}
		class="policy-point-label"
		onclick={(ev) => selectPolicy(ev)}
		>P{(policy.index ?? 0) + 1}: {policy.name?.substring(0, 20)}...</text
	>
{/if}

<style>
	.policy-point {
		cursor: pointer;
	}

	.policy-point-label {
		cursor: pointer;
		font-size: x-small;
		font-weight: 600;
		paint-order: stroke;
		stroke: #ffffffb0;
		stroke-width: 3px;
		stroke-linecap: butt;
		stroke-linejoin: miter;
	}

	.policy-point-icon {
		cursor: pointer;
		font-size: small;
		font-weight: 600;
	}
</style>
