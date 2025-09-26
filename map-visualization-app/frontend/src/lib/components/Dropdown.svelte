<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
	import { ChevronDownOutline } from 'flowbite-svelte-icons';
	import { onMount } from 'svelte';

	export let options: string[] = [];
	export let selected: string;
	export let classNames: string;

	let isOpen = false;
	let dropdownElement: HTMLElement;

	export let placeholder: string = 'Select option...';
	export let title: string = 'select option';
	export let label: string = '';

	function toggleDropdown() {
		isOpen = !isOpen;
	}

	function selectOption(option: string) {
		selected = option;
		isOpen = false;
	}

	function handleClickOutside(event: MouseEvent) {
		if (dropdownElement && !dropdownElement.contains(event.target as Node) && isOpen) {
			isOpen = false;
		}
	}

	onMount(() => {
		document.addEventListener('click', handleClickOutside);
		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions a11y-no-noninteractive-element-interactions -->
<div class="relative w-full dropdown {classNames}">
	{#if label}
		<b>{label}</b>
	{/if}
	<div bind:this={dropdownElement}>
		<div class="selected" onclick={toggleDropdown} class:opened={isOpen} {title}>
			{selected || placeholder}
			<span class="arrow" class:rotate={isOpen}><ChevronDownOutline /></span>
		</div>
		{#if isOpen}
			<ul class="options">
				{#each options as option}
					<li onclick={() => selectOption(option)}>{option}</li>
				{/each}
			</ul>
		{/if}
	</div>
</div>

<style lang="scss">
	.dropdown {
		&:not(:last-child) {
			margin-bottom: 0.75rem;
		}

		b {
			display: block;
			margin-bottom: 0.25rem;
		}

		.selected {
			border: 1px solid var(--color-border-dark);
			border-radius: 0.5rem;
			display: flex;
			justify-content: space-between;
			align-items: center;

			&:hover {
				border-color: var(--color-accent-med);
			}

			&.opened {
				border-color: var(--color-accent);
				border-radius: 0.5rem 0.5rem 0 0;
			}

			.arrow {
				transition: 0.3s;
				&.rotate {
					transform: rotate(180deg);
				}
			}
		}

		.selected,
		li {
			cursor: pointer;
			padding: 0.4rem 0.5rem 0.4rem 0.75rem;
			transition: 0.3s;
		}

		.options {
			position: absolute;
			top: 100%;
			left: 0;
			right: 0;
			background: white;
			border: 1px solid var(--color-border-dark);
			border-top: none;
			border-radius: 0 0 0.5rem 0.5rem;
			list-style: none;
			padding: 0;
			margin: 0;
			max-height: 200px;
			overflow-y: auto;
			transition: 0.3s;
			z-index: 2;
		}

		li {
			cursor: pointer;
		}

		li:hover {
			background-color: var(--color-border-light);
		}
	}
</style>
