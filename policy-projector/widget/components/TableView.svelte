<!--
  For licensing see accompanying LICENSE file.
  Copyright (C) 2025 Apple Inc. All Rights Reserved.
-->

<script>
    // Component to render a table of text examples
    import { onMount } from "svelte";
    import { Heading, List, Li, Input, Button } from "flowbite-svelte";

    // Properties
    export let model;

    // Input data processing
    let name = model.get("name");
    let cur_id = model.get("id");
    let colSettings = model.get("col_settings");
    let colTypes = model.get("col_types");
    let metadata = model.get("metadata");
    handleMetadataChange();  // initialize to avoid missing first update
    let rows = model.get("rows"); // Fetch data for table
    let showTableSaveButton = hasEditableCols(colSettings);

    // Table setup
    let isLoaded = false;
    onMount(async () => {
        await import("active-table");
        isLoaded = true;
    });

    function hasEditableCols(settings) {
        for (let setting of settings) {
            if (setting["isCellTextEditable"]) {
                return true;
            }
        }
        return false;
    }

    // Handle data changes in table
    function handleCellUpdate(update) {
        if (update.updateType == "Update") {
            model.set("rows_updated", []);
            model.save_changes();
            model.set("rows_updated", rows);
            model.save_changes();
        }
    }

    function handleMetadataChange() {
        const newMetadata = Object.assign({}, metadata); // Make copy to trigger update
        model.set("metadata", newMetadata);
        model.save_changes();
    }

    function saveTable() {
        model.set("save_table", true);
        model.save_changes();
    }
</script>

<div class="wrapper">
    <Heading tag="h4" class="mb-4">{name} <code>(ID: {cur_id})</code></Heading>
    {#if metadata}
        {#each Object.entries(metadata) as [title, value]}
            <div class="mb-4">
            {#if Array.isArray(value)}
                <Heading tag="h6" class="mb-2">{title}:</Heading>
                <List tag="ul" class="space-y-1">
                    {#each value as item}
                        <Li>{item}</Li>
                    {/each}
                </List>
            {:else}
                <Heading tag="h6" class="mb-2">{title}:</Heading>
                <div>
                    <Input id={title} size="lg" bind:value={metadata[title]} >
                        <Button size="sm" color="alternative" type="submit" onclick={handleMetadataChange}>Submit</Button>
                    </Input>
                </div>
            {/if}
            </div>
        {/each}
    {/if}
    <Heading tag="h6">Examples ({rows.length - 1}):</Heading>
    {#if isLoaded}
        <div class="table-container">
            <active-table
                data={rows}
                onCellUpdate={handleCellUpdate}
                filter={[
                    {
                        placeholderTemplate: "Filter by {headerName}",
                        position: "top-left",
                        order: 1,
                        styles: { input: { width: "200px" } },
                    },
                ]}
                pagination={{ rowsPerPage: 5 }}
                stickyHeader={true}
                isCellTextEditable={false}
                displayAddNewRow={false}
                displayAddNewColumn={false}
                dragRows={false}
                customColumnTypes={colTypes}
                customColumnsSettings={colSettings}
                rowDropdown={{
                    isDeleteAvailable: false,
                    isInsertUpAvailable: false,
                    isInsertDownAvailable: false,
                    canEditHeaderRow: false,
                }}
                columnDropdown={{
                    isDeleteAvailable: false,
                    isInsertLeftAvailable: false,
                    isInsertRightAvailable: false,
                }}
                tableStyle={{ borderRadius: "8px" }}
                headerStyles={{ default: { backgroundColor: "#ebebeb" } }}
            ></active-table>
        </div>
        
        {#if showTableSaveButton}
        <div class="wrapper">
            <Button size="sm" color="alternative" onclick={saveTable}>Save table edits to {name}</Button>
        </div>
        {/if}
    {/if}
</div>

<style>
    @import "../app.css";

    .wrapper {
        margin: 10px;
    }

    .table-container {
        overflow-x: scroll;
        padding: 20px 0;  /* vertical padding to avoid overlap of scrollbar with table elems */
    }
</style>
