/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { coordinator } from "@uwdata/mosaic-core";
import {
  datasetOptions,
  mapTable,
  mapReady,
  pointCount,
  getOrInitializeClient,
  mapSelectedPoints,
} from "./store";
import type {
  ConceptGroup,
  Filter,
  Policy,
  Concept,
  PolicyFilter,
  ConceptFilter,
} from "./types";
import { isConceptFilter, isPolicyFilter } from "./types";
import {
  initializeDatabase,
  initializeDuckDB,
  loadProjectionTable,
  loadConceptFeatureTable,
  loadReprojection,
} from "$lib/mosaic/loader.js";
import {
  createBaseTableView,
  createReprojectedView,
} from "./mosaic/tableViews";
import {
  baseProjectionTableName,
  baseTableView,
  categoricalTableName,
  featureTableName,
} from "./constants";
import { getTableLength } from "$lib/mosaic/helperQueries";

let DEBUG = true; // Change to false for production
let prod_server = ""; // Set your sever location here
let local_server = "http://localhost";

// Default to the same server.
let server_prefix = DEBUG ? `${local_server}:9001` : `${prod_server}:9001`;

// In HMR mode, we use the server at localhost:9001 (the default of the web_server module).
if (import.meta.hot) {
  server_prefix = DEBUG ? `${local_server}:9001` : `${prod_server}:9001`;
}

export async function fetchDatasetOptions(
  fetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
) {
  const res = await fetch(server_prefix + "/datasets");
  const datasets = (await res?.json())?.datasets;
  if (datasets) datasetOptions.set(datasets.sort());
}

export async function fetchConceptList(dataset: string) {
  const res = await fetch(server_prefix + "/conceptlist/" + dataset);
  const concepts: ConceptGroup[] = (await res?.json()) ?? [];
  console.log("Concepts loaded:", concepts);
  return concepts;
}

export async function fetchPolicies(dataset: string) {
  const res = await fetch(server_prefix + "/policy/" + dataset);
  const policies: Policy[] = (await res?.json()) ?? [];
  console.log("Policies loaded!", policies);
  return policies;
}

export async function addConcept(dataset: string, conceptSpec: string) {
  const endpoint = server_prefix + "/conceptadd/" + dataset;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ conceptSpec: conceptSpec }),
  });
  const resParsed = await res?.json();
  console.log("Added concept:", resParsed["concept_name"]);
}

export async function refreshConceptsAndMap(
  dataset: string,
  concept?: Concept,
  policy?: Policy
) {
  // Update concept list and map in UI
  mapReady.set(false);
  mapTable.set(baseTableView);
  mapSelectedPoints.set([]);
  const conceptList = await fetchConceptList(dataset);
  const policyList = await fetchPolicies(dataset);
  loadDataset(dataset).then(async () => {
    let client = getOrInitializeClient(conceptList, policyList);

    await client.computeConceptMap();
    await client.computePolicyMap();
    // Clear filters and filter to the new concept or policy (if provided)
    if (concept) {
      client.removeAllFilters();
      client.filterByConcept(concept);
    } else if (policy) {
      client.removeAllFilters();
      client.filterByPolicy(policy);
    }

    mapReady.set(true);
  });
}

export async function fetchLatentConcepts(
  dataset: string,
  filterList: Filter[]
) {
  let filterKeys = filterList.map((f) => {
    if (isConceptFilter(f)) return f.concept.name;
    else if (isPolicyFilter(f)) return f.policy.name;
  });
  console.log("Fetch latent concepts for ", dataset, filterKeys);

  const latentConceptsURL = server_prefix + "/latentConcepts/" + dataset;
  const request = new Request(latentConceptsURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ concepts: filterKeys }),
  });

  const res = await fetch(request);
  if (res.status == 200) {
    console.log("Latent concepts created!");
    await refreshConceptsAndMap(dataset);
  }
}

export async function conceptFindSimilar(
  dataset: string,
  concept: Concept,
  limit: number
) {
  const endpoint = server_prefix + "/conceptFindSimilar/" + dataset;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ concept: concept, limit: limit }),
  });
  const resParsed = await res?.json();
  return resParsed["example_ids"];
}

export async function policyFindMatches(
  dataset: string,
  policy: Policy,
  limit: number
) {
  const endpoint = server_prefix + "/policyFindMatches/" + dataset;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ policy: policy, limit: limit }),
  });
  const resParsed = await res?.json();
  return resParsed["example_ids"];
}

export async function conceptMetadataSave(dataset: string, concept: Concept) {
  const endpoint = server_prefix + "/conceptMetadataSave/" + dataset;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ concept: concept }),
  });
  const resParsed = await res?.json();
  if (resParsed["changed_examples"] == true) {
    await refreshConceptsAndMap(dataset, concept);
  }
  return resParsed["message"];
}

export async function policyMetadataSave(dataset: string, policy: Policy) {
  const endpoint = server_prefix + "/policyMetadataSave/" + dataset;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ policy: policy }),
  });
  const resParsed = await res?.json();
  if (resParsed["changed_examples"] == true) {
    await refreshConceptsAndMap(dataset, undefined, policy);
  }
  return resParsed["message"];
}

export async function conceptCreate(dataset: string, concept: Concept) {
  const endpoint = server_prefix + "/conceptCreate/" + dataset;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ concept: concept }),
  });
  const resParsed = await res?.json();
  await refreshConceptsAndMap(dataset, concept);
  return resParsed["message"];
}

export async function policyCreate(dataset: string, policy: Policy) {
  const endpoint = server_prefix + "/policyCreate/" + dataset;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ policy: policy }),
  });
  const resParsed = await res?.json();
  const policyIndex = resParsed["policy_index"];
  const policyId = resParsed["policy_id"];
  policy.index = policyIndex;
  policy.id = policyId;
  await refreshConceptsAndMap(dataset, undefined, policy);
  return resParsed["message"];
}

export async function loadDataset(datasetName: string) {
  // start up DuckDB
  await initializeDuckDB();

  // reset from any previous data sessions
  coordinator().clear();

  // load in the tabular data for this dataset
  await loadParquet(datasetName);

  // load in concept features for this dataset
  await loadConceptFeatures(datasetName);

  // now load in the initial projections for this dataset
  await loadProjection(datasetName);

  // now create views
  await createBaseTableView();

  // show point count
  let count = await getTableLength(baseTableView);
  pointCount.set(count);
}

export async function reproject(datasetName: string, filterList: Filter[]) {
  // TODO refine filter predicate
  let filterKeys = filterList.map((f) => {
    if (isConceptFilter(f)) return f.concept.name;
    else if (isPolicyFilter(f)) return f.policy.name;
  });
  console.log("Reproject for ", datasetName, filterKeys);

  const reprojectURL = server_prefix + "/reproject/" + datasetName;
  const request = new Request(reprojectURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ concepts: filterKeys }),
  });
  console.log("Request", request);

  const res = await fetch(request);
  // it worked
  if (res.status == 200) {
    mapReady.set(false);
    const resParsed = await res?.json();
    let requestID = resParsed["request_id"]; // req ID prevents DuckDB caching of the parquet file
    console.log("Response!", resParsed);

    // load new projection on frontend
    const parquetURL =
      server_prefix + "/reprojection/" + datasetName + "?reqID=" + requestID;
    const islandName =
      filterKeys.map((key) => key?.replace(/\W/g, "") ?? "").join("-") +
      "_island";
    await loadReprojection(parquetURL, islandName);
    const viewName = await createReprojectedView(islandName);
    mapTable.set(viewName);
    mapReady.set(true);
  }
}

export function getAcronym(conceptName: string) {
  // Get short acronym to display in diagrams
  const titleCase = (s: string) =>
    s.replace(/^_*(.)|_+(.)/g, (s, c, d) =>
      c ? c.toUpperCase() : " " + d.toUpperCase()
    );

  const acronym = (s: string) =>
    s
      .split(/\s/)
      .reduce(
        (accumulator: string, word: string) => accumulator + word.charAt(0),
        ""
      );

  let displayName = titleCase(conceptName);
  let displayAcronym = acronym(displayName).replace(/[0-9]/g, "");
  return displayAcronym;
}

export function getFocusedConcepts(
  activeFilters: Filter[],
  conceptList: ConceptGroup[]
) {
  // Fetch concepts from concept-filters
  let conceptFiltersConcepts = activeFilters
    .filter((f: Filter) => isConceptFilter(f))
    .map((f: ConceptFilter) => f.concept);
  // Fetch concepts from policy-filters
  let policyFilterConcepts = activeFilters
    .filter((f: Filter) => isPolicyFilter(f))
    .flatMap((f: PolicyFilter) => {
      let conceptNames = f.policy.if; // Get if-condition concept names
      let concepts = conceptList.flatMap((group: ConceptGroup) =>
        group.concepts.filter((c) => conceptNames.includes(c.name))
      ); // Get concepts
      return concepts;
    });
  let concepts = conceptFiltersConcepts.concat(policyFilterConcepts);
  return concepts;
}

export function getFocusedPolicies(activeFilters: Filter[]) {
  // Fetch concepts from policy-filters
  let policies = activeFilters
    .filter((f: Filter) => isPolicyFilter(f))
    .flatMap((f) => f.policy);
  return policies;
}

export async function regenerateData(dataset: string) {
  const res = await fetch(server_prefix + "/regenerateData/" + dataset);
  await refreshConceptsAndMap(dataset);
}

/*
 * ########### Helper Functions ####################
 */

async function loadParquet(datasetName: string) {
  const parquetURL = server_prefix + "/tabular/" + datasetName + ".parquet";
  await initializeDatabase(parquetURL, categoricalTableName);
}

async function loadConceptFeatures(datasetName: string) {
  const conceptFeatURL = server_prefix + "/features/" + datasetName;
  await loadConceptFeatureTable(conceptFeatURL, featureTableName);
}

async function loadProjection(datasetName: string) {
  const projectionURL = server_prefix + "/projection/" + datasetName;
  await loadProjectionTable(projectionURL, baseProjectionTableName);
}
