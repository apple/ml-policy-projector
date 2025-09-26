<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { bottomTrayHeight, mapFilter, caseTableRows, caseTableHeaders } from '$lib/store';
	import { bottomDrawerClosedHeight, categoricalTableName } from '$lib/constants';
	import {
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';
	import { onMount } from 'svelte';
	import { CaseTableClient } from '$lib/mosaic/caseTableClient';
	import { coordinator } from '@uwdata/mosaic-core';

	// Mosaic client
	let client: CaseTableClient;

	onMount(() => {
		// initialize client the first time the table appears
		client = new CaseTableClient({
			filterBy: $mapFilter,
			as: $mapFilter,
			fromTable: categoricalTableName
		});
		coordinator().connect(client);
	});

	let prevScrollTop = -1;

	function scrolledTable(evt: Event) {
		const { scrollHeight, scrollTop, clientHeight } = evt.target as Element;
		const { pending, loaded } = client;

		const back = scrollTop < prevScrollTop;
		prevScrollTop = scrollTop;
		if (back || pending || loaded) return;

		if (scrollHeight - scrollTop < 2 * clientHeight) {
			//client.requestMoreData();
			console.log('WE NEED MORE DATA');
		}
	}
</script>

<section class="overflow-y-scroll">
	<div
		class="tableWrapper p-4"
		style="max-height: calc({$bottomTrayHeight - bottomDrawerClosedHeight}px)"
		on:scroll={scrolledTable}
	>
		<Table hoverable={true} class="w-full">
			<TableHead class="border-b sticky top-0">
				{#each $caseTableHeaders ?? [] as h}
					<TableHeadCell class="tableCellHeader overflow-hidden">{h}</TableHeadCell>
				{/each}
			</TableHead>
			<TableBody class="h-72 overflow-y-visible">
				{#each $caseTableRows || ['', '', ''] as row}
					<TableBodyRow class="">
						{#each row as item}
							<TableBodyCell class="tableCell"
								><div class="tableCellContent">{item}</div></TableBodyCell
							>
						{/each}
					</TableBodyRow>
				{/each}
			</TableBody>
		</Table>
	</div>
</section>
