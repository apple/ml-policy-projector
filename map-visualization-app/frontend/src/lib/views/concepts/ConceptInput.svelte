<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { Textarea, Label, GradientButton } from 'flowbite-svelte';
	import { currentDataset } from '$lib/store';
	import { addConcept } from '$lib/api';

	let spec = '';
	let dataset = '';

	currentDataset.subscribe((value) => {
		dataset = value;
	});
 
	async function handleAddConcept() {
		console.log('Adding concept');
		await addConcept(dataset, spec);
	}
</script>

<section class="">
	<h3 class="pb-2">Manually add a concept</h3>
	<Label for="concept-input" class="mb-2">Concept Spec</Label>
	<Textarea
		id="concept-input"
		bind:value={spec}
		placeholder="Paste concept spec here"
		rows={4}
		name="spec"
	/>
	<GradientButton size="xs" outline color="pinkToOrange" onclick={handleAddConcept}
		>Add</GradientButton
	>
</section>
