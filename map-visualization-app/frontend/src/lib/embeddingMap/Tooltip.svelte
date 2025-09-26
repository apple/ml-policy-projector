<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import type { DataPoint } from 'embedding-atlas';
	export let tooltip: DataPoint;
	export let inputField: string;
	export let harmField: string;

	let parseField = (t: DataPoint, field: string) => {
		if(t.fields) {
			return t.fields[field]?.toString() ?? '(null)';
		}
		return '(null)';
	};
</script>

<div
	class="p-2 border flex flex-col gap-2 border-gray-500 shadow-md bg-white dark:bg-gray-800 rounded-md select-none overflow-x-hidden overflow-y-scroll"
	style:max-width="400px"
	style:max-height="350px"
>
	<div class="flex-none text-ellipsis overflow-hidden" style:max-height="150px">
		<h4 class="text-xs uppercase">Input</h4>
		<div class="p-1 bg-gray-50 text-gray-700 rounded-md">
			<p class="text-xs">{parseField(tooltip, inputField)}</p>
		</div>
	</div>
	<div class="flex-none text-ellipsis overflow-hidden" style:max-height="150px">
		<h4 class="text-xs uppercase">Output</h4>
		<div class="p-1 bg-gray-50 text-gray-700 rounded-md">
			<p class="text-xs">{tooltip.text}</p>
		</div>
	</div>
	<div class="flex-none">
		<h4 class="text-xs uppercase">Harms</h4>
		<div class="p-1 bg-gray-50 text-gray-700 rounded-md">
			<p class="harm-text">{parseField(tooltip, harmField)}</p>
		</div>
	</div>
</div>

<style>
	.harm-text {
		font-size: 9px;
	}
</style>
