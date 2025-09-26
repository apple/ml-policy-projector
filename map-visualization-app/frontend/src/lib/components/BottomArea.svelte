<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { Accordion, AccordionItem } from 'flowbite-svelte';
	import { bottomTrayOpen } from '$lib/store';

	let {activeSection = 0, sectionTitles, children} = $props()

	function selectSection(ev: Event, index: number) {
		ev.preventDefault();
		ev.stopPropagation();
		activeSection = index;
	}
</script>

<section class="bottom-area fixed bottom-0 z-40 w-full bg-white">
	<Accordion flush>
		<AccordionItem
			bind:open={$bottomTrayOpen}
			class="w-full flex justify-between p-4 border-t !rounded-none"
		>
			{#snippet header()}
				<div class="flex flex-row gap-4 text-sm">
					{#each sectionTitles as title, index}
						<button
							class={`cursor-pointer pb-1 border-b-2 ${index == activeSection ? 'text-accent border-accent' : 'text-secondary border-transparent'}`}
							onclick={(ev) => selectSection(ev, index)}
							>{title}
						</button>
					{/each}
				</div>
			{/snippet}

			<div class="px-4 min-h-72">
				{@render children?.()}
			</div>
		</AccordionItem>
	</Accordion>
</section>

<style lang="scss">
	.bottom-area {
		transition: 0.3s;
	}
</style>
