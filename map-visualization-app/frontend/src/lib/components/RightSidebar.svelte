<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { ChevronRightOutline, ChevronLeftOutline } from 'flowbite-svelte-icons';
	import { rightSidebarOpen } from '../store';
	let { children } = $props();

	const toggleSidebar = () => {
		rightSidebarOpen.set(!$rightSidebarOpen);
	};
</script>

<section class="fixed h-full right-0 z-10 sidebar" class:collapsed={!$rightSidebarOpen}>
	<button
		class="absolute top-0 left-0 z-40 px-2 py-4 bg-sidebar icon-tab hover:text-accent"
		onclick={toggleSidebar}
	>
		{#if $rightSidebarOpen}<ChevronRightOutline />
		{:else}<ChevronLeftOutline />{/if}
	</button>
	<div class="sidebar-content px-4 py-2 bg-sidebar h-full" class:hidden={!$rightSidebarOpen}>
		<!-- Sidebar contents go here -->
		{@render children?.()}
	</div>
</section>

<style lang="scss">
	.sidebar {
		&.collapsed {
			transform: translateX(100%);
		}
	}

	.sidebar-content {
		&.hidden {
			visibility: hidden;
			pointer-events: none;
		}
	}

	.icon-tab {
		border-radius: 10px 0 0 10px;
		transform: translateX(-100%);
		transition: 0.3s;
	}
</style>
