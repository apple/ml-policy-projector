<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import LeftSidebar from '$lib/components/LeftSidebar.svelte';
	import MainArea from '$lib/components/MainArea.svelte';
	import { mapTable, mapReady, caseTableSize, bottomTrayHeight } from '$lib/store';
	import { appName, bottomDrawerClosedHeight, bottomDrawerOpenHeight } from '$lib/constants';
	import RightSidebar from '$lib/components/RightSidebar.svelte';
	import BottomTray from '$lib/components/BottomTray.svelte';
	import EmbeddingMap from '$lib/embeddingMap/EmbeddingMap.svelte';
	import MapSettings from '$lib/embeddingMap/MapSettings.svelte';
	import MapUIOverlay from '$lib/embeddingMap/ui-overlays/MapUIOverlay.svelte';
	import { DrawerView } from '$lib/constants';
	import CaseTable from '$lib/views/table/CaseTable.svelte';
	import ConceptSandbox from '$lib/views/concepts/ConceptSandbox.svelte';
	import PolicySandbox from '$lib/views/policy/PolicySandbox.svelte';
	import { Tabs, TabItem, Spinner } from 'flowbite-svelte';
	import { AngleUpOutline, AngleDownOutline } from 'flowbite-svelte-icons';

	// Page dimensions
	$: innerWidth = 0;
	$: innerHeight = 0;
	$: bottomTrayOpen = $bottomTrayHeight > bottomDrawerClosedHeight;

	let lastAction: number;
	function toggleBottomTrayHeight(curAction: number) {
		// Set larger height for policy authoring
		let maxHeight = curAction == DrawerView.AddPolicy ? 500 : bottomDrawerOpenHeight;
		if (lastAction == curAction || curAction == DrawerView.Collapse) {
			// Clicking on same tab
			if (bottomTrayOpen) {
				// Minimize
				bottomTrayHeight.set(bottomDrawerClosedHeight);
			} else {
				// Expand
				bottomTrayHeight.set(maxHeight);
			}
		} else {
			// Clicking on different tab
			if (!bottomTrayOpen) {
				// Expand if tray is closed
				bottomTrayHeight.set(maxHeight);
			} else if (curAction == DrawerView.AddPolicy) {
				// Make larger if changed to policy authoring
				bottomTrayHeight.set(maxHeight);
			} // Otherwise maintain height
		}
		lastAction = curAction;
	}
</script>

<svelte:window bind:innerWidth bind:innerHeight />

<svelte:head>
	<title>{appName}</title>
	<meta name="description" content={appName} />
</svelte:head>

<section class="flex flex-col">
	<!-- horizontal main area -->
	<div class="flex flex-row flex-1">
		<!-- Left Sidebar -->
		<LeftSidebar height={innerHeight - $bottomTrayHeight} />

		<!-- Map Area -->
		<MainArea>
			{#if $mapReady}
				{#key $mapTable}
					<EmbeddingMap tableName={$mapTable} width={innerWidth} height={innerHeight} />
				{/key}
			{/if}
			<MapUIOverlay />
		</MainArea>

		<!-- Right Sidebar -->
		<RightSidebar>
			<MapSettings />
		</RightSidebar>
	</div>

	<!-- BottomTray -->
	<div class="w-full overflow-auto">
		<BottomTray maxHeight={innerHeight }>
			<Tabs tabStyle="underline" class="z-40 bg-white w-full">
				<!-- Show tabs, but don't fetch content or enable clicking unless map is ready -->
				<TabItem
					open
					title="Concept authoring"
					onclick={() => toggleBottomTrayHeight(DrawerView.AddConcept)}
					disabled={!$mapReady}
				>
					{#if $mapReady}
						<ConceptSandbox />
					{:else}
						<div class="max-w-full mt-10 flex place-content-center">
							<Spinner color="gray" size="6" />
						</div>
					{/if}
				</TabItem>
				<TabItem
					title="Policy authoring"
					onclick={() => toggleBottomTrayHeight(DrawerView.AddPolicy)}
					disabled={!$mapReady}
				>
					{#if $mapReady}
						<PolicySandbox />
					{:else}
						<div class="max-w-full mt-10 flex place-content-center">
							<Spinner color="gray" size="6" />
						</div>
					{/if}
				</TabItem>
				<TabItem
					title={`Table ${$caseTableSize ? '(' + $caseTableSize + ')' : ''}`}
					onclick={() => toggleBottomTrayHeight(DrawerView.DataTable)}
					disabled={!$mapReady}
				>
					{#if $mapReady}
						<CaseTable />
					{:else}
						<div class="max-w-full mt-10 flex place-content-center">
							<Spinner color="gray" size="6" />
						</div>
					{/if}
				</TabItem>
				<div
					class="place-content-center inline-block"
					style="margin-left: auto; margin-right: 10px;"
				>
					<button onclick={() => toggleBottomTrayHeight(DrawerView.Collapse)}>
						{#if bottomTrayOpen}
							<AngleDownOutline />
						{:else}
							<AngleUpOutline />
						{/if}
					</button>
				</div>
			</Tabs>
		</BottomTray>
	</div>
</section>
