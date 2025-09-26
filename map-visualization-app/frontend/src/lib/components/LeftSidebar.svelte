<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { Tabs, TabItem } from 'flowbite-svelte';
	import { leftSidebarOpen } from '../store';
	import {
		appClient,
		showConceptMarkers,
		showLatentConceptMarkers,
		showPolicyMarkers
	} from '$lib/store';
	import PolicyList from '$lib/views/policy/PolicyList.svelte';
	import ConceptPane from '$lib/views/concepts/ConceptPane.svelte';

	export let height;
	let heightBuffer = 25;

	const toggleSidebar = () => {
		leftSidebarOpen.set(!$leftSidebarOpen);
	};

	const handleConceptPaneSelect = () => {
		$appClient?.removeAllFilters();
		$showConceptMarkers = true;
		$showLatentConceptMarkers = true;
		$showPolicyMarkers = false;
	};

	const handlePolicyPaneSelect = () => {
		$appClient?.removeAllFilters();
		$showPolicyMarkers = true;
		$showConceptMarkers = false;
		$showLatentConceptMarkers = false;
	};
</script>

<section class="fixed h-full z-10 sidebar" class:collapsed={!$leftSidebarOpen}>
	<div
		class="sidebar-content px-4 py-2 bg-sidebar overflow-auto"
		class:hidden={!$leftSidebarOpen}
		style="height: calc({height - heightBuffer}px)"
	>
		<Tabs tabStyle="underline" class="p-4">
			<TabItem open title="Concepts" onclick={handleConceptPaneSelect}>
				<ConceptPane />
			</TabItem>
			<TabItem title="Policy" onclick={handlePolicyPaneSelect}>
				<PolicyList />
			</TabItem>
		</Tabs>
	</div>
</section>

<style lang="scss">
	.sidebar {
		&.collapsed {
			transform: translateX(-100%);
		}
	}

	.sidebar-content {
		&.hidden {
			visibility: hidden;
			pointer-events: none;
		}
	}
</style>
