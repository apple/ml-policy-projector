<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script>
	import Header from '$lib/components/Header.svelte';
	import { appName } from '$lib/constants';
	import '../app.css';
	let { children } = $props();
</script>

<div class="h-screen">
	<Header title={appName} />
	<main>
		{@render children?.()}
	</main>
</div>
