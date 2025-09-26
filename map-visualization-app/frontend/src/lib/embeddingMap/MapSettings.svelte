<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { colorBy } from '$lib/store';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import ConceptInput from '$lib/views/concepts/ConceptInput.svelte';

	const colorOptions = ['default', 'category'];
</script>

<div>
	<h3 class="pb-2">Map Options</h3>
	<Dropdown
		classNames=""
		options={colorOptions}
		bind:selected={$colorBy}
		placeholder={'Select color by...'}
		label={'Color by'}
		title={'select color by'}
	/>

	<div class="mt-10">
		<ConceptInput />
	</div>
</div>