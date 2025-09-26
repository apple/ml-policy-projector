<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script lang="ts">
    import { bottomTrayHeight } from '$lib/store';
    let { maxHeight, children } = $props();

    let height = $bottomTrayHeight;
    let expanding = false;
    let startY = 0;
    let startHeight = 0;
    const defaultHeight = 60;
    const minHeight = 60;
    

    function startExpanding(ev: MouseEvent) {
        startY = ev.screenY;
        expanding = true;
        startHeight = $bottomTrayHeight;
    }

    function stopExpanding() {
        if (height < minHeight) {
            height = defaultHeight;
            bottomTrayHeight.set(defaultHeight);
        }
        expanding = false;
        startY = 0;
        startHeight = height;
    }
    
    function expand(ev: MouseEvent) {
        if (expanding) {
            height = Math.min(maxHeight, startHeight + (startY - ev.screenY));
            bottomTrayHeight.set(height);
            ev.stopPropagation();
            ev.preventDefault();
        }
    }
</script>

<svelte:window onmousemove={(ev) => expand(ev)} on:mouseup={() => stopExpanding()} />
<div
    class="absolute bottom-0 bg-white z-50 w-full p-0"
    style="height: calc({$bottomTrayHeight}px)"
>   
    <div class="flex flex-col">
        <!-- Top grab bar to resize lower page section -->
        <button
            class="w-full h-1.5 sticky bg-gray-200 cursor-row-resize hover:bg-gray-300 click:bg-gray-400"
            onmousedown={(ev) => startExpanding(ev)}
            aria-label="A grabber to expand the lower page section"
        ></button>
        <!-- Content -->
        {@render children?.()}
    </div>
</div>
