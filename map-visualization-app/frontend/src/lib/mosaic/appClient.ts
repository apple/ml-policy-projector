/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import {
  type ConceptGroup,
  type Filter,
  type Concept,
  type ConceptFilter,
  type Policy,
  type PolicyFilter,
  isConceptFilter,
  isPolicyFilter,
} from "$lib/types";
import { MosaicClient } from "@uwdata/mosaic-core";
import { sql, TableRefNode, and } from "@uwdata/mosaic-sql";
import { baseTableView, featureTableName } from "$lib/constants";
import {
  activeFilters,
  conceptList,
  policyList,
  mapTable,
  showNone,
  pointCount,
  showOverlay,
} from "$lib/store";
import { getTableLength } from "./helperQueries";
import * as db from "./appQueries";

const DEBUG = false;

export class AppClient extends MosaicClient {
  constructor(ops: {
    filterBy: Selection;
    as: Selection;
    conceptList: ConceptGroup[];
    policyList: Policy[];
    projectionTable: String;
    showingNone: Boolean;
  }) {
    super(ops.filterBy);
    this.selection = ops.as;
    this.conceptList = ops.conceptList;
    conceptList.set(this.conceptList);
    this.policyList = ops.policyList;
    policyList.set(this.policyList);
    this.projectionTable = ops.projectionTable;
    this.activeConcepts = [] as ConceptFilter[];
    this.showingNone = ops.showingNone;
    showNone.set(this.showingNone);

    // stay aligned
    mapTable.subscribe(async (value) => {
      if (value) {
        this.projectionTable = value;
        // update centroids when the map changes
        this.conceptList = await db.updateCentroids(
          this.conceptList,
          this.getFilter(),
          this.projectionTable
        );
        this.policyList = await db.updatePolicyCentroids(
          this.policyList,
          this.getFilter(),
          this.projectionTable
        );
      }
    });
    showNone.subscribe((value: boolean) => this.showNone(value));
    conceptList.subscribe((value) => (this.conceptList = value ?? []));
    policyList.subscribe((value) => (this.policyList = value ?? []));
  }

  showNone(flag: boolean, noneKey: string = "safe") {
    if (flag !== this.showingNone) {
      this.showingNone = flag;
      this.publish();
    }
  }

  filterAll() {
    const meta = { type: "hide" };
    let predicate = sql`false`;
    this.selection.update({ meta, source: this, value: "hide", predicate });
  }

  removeFilter(filter: Filter) {
    this.activeConcepts = this.activeConcepts.filter(
      (c: Filter) => c.display_name !== filter.display_name
    );
    if (this.activeConcepts.length < 1) {
      this.resetMap();
      // show overlay markers
      showOverlay.set(true);
    }
    this.publish();
  }

  removeAllFilters() {
    this.activeConcepts = [];
    this.resetMap();
    // show overlay markers
    showOverlay.set(true);
    this.publish();
  }

  resetMap() {
    mapTable.set(baseTableView);
  }

  async computeConceptMap() {
    const filter = this.getFilter();
    const projectionTable = this.projectionTable;
    if (DEBUG)
      console.log("Recomputing!", this.conceptList, filter, projectionTable);
    let concepts = this.conceptList;
    await Promise.all(
      concepts?.map(async (group: ConceptGroup) => {
        // get details for concepts
        await Promise.all(
          group.concepts?.map(async (c) => {
            c.count = await db.sumColumn(c.name, filter);
            c.centroid = await db.getMedianPos(c.name, filter, projectionTable);
          })
        );
        // get details for "none" concept
        if (group.none?.name) {
          group.none.count = await db.sumColumn(group.none?.name, filter);
          group.none.centroid = await db.getMedianPos(
            group.none.name,
            filter,
            projectionTable
          );
        }
      })
    );

    if (DEBUG) console.log("new concepts are", concepts);
    conceptList.set(concepts);
  }

  async computePolicyMap() {
    const filter = this.getFilter();
    const projectionTable = this.projectionTable;
    if (DEBUG)
      console.log("Recomputing!", this.policyList, filter, projectionTable);
    let policies = this.policyList;
    await Promise.all(
      policies?.map(async (p: Policy) => {
        // get details for policies
        p.count = await db.sumPolicyColumns(p, filter);
        p.centroid = await db.getPolicyMedianPos(p, filter, projectionTable);
      })
    );

    this.policyList = policies;
    policyList.set(policies);
  }

  async filterByConcept(concept: Concept) {
    let filtered = this.activeConcepts.find(
      (f: ConceptFilter) => f.display_name === concept.display_name
    );
    if (filtered) this.removeFilter(filtered);
    else {
      this.activeConcepts.push({
        display_name: concept.display_name,
        concept,
      });
      // hide overlay markers
      showOverlay.set(false);
      this.publish();
    }
  }

  async filterByPolicy(policy: Policy) {
    let filtered = this.activeConcepts.find(
      (f: PolicyFilter) => f.policy.id === policy.id
    );
    if (filtered) this.removeFilter(filtered);
    else {
      this.activeConcepts.push({
        display_name: "Policy " + ((policy.index ?? 0) + 1),
        policy,
      });
      // hide overlay markers
      showOverlay.set(false);
      this.publish();
    }
  }

  async publish() {
    activeFilters.set(this.activeConcepts);
    await this.selection.update(this.getClauses());
    const filters = this.getFilter();
    this.computeConceptMap();
    this.computePolicyMap();
    let count = await getTableLength(this.projectionTable, filters);
    pointCount.set(count);
  }

  getFilter() {
    return this.filterBy?.predicate(this)?.toString();
  }

  getClauses() {
    let clauses = this.activeConcepts.map((c: Filter) => {
      if (isConceptFilter(c)) {
        return this.__predicate_concept(c.concept);
      } else if (isPolicyFilter(c)) {
        return this.__predicate_policy(c.policy);
      }
    });
    if (this.showingNone == false) {
      clauses.push(this.__predicate_hideNone());
    }
    let expr = clauses.length > 1 ? and(clauses) : clauses[0];
    return { source: this, value: "conceptFilter", predicate: expr };
  }

  __predicate_concept(concept: Concept) {
    const table = new TableRefNode(featureTableName);
    const conceptName = concept.name;
    return sql`rowID in (
			SELECT rowID from ${table} WHERE "${conceptName}" == 1
		)`;
  }

  __predicate_policy(policy: Policy) {
    let conceptNames = policy.if;
    if (conceptNames.length == 0) return "";
    let conceptFilters = conceptNames.map((c) => `"${c}" == 1`);
    let conceptsFormatted = conceptFilters.join(" AND ");
    const table = new TableRefNode(featureTableName);
    return sql`rowID in (
			SELECT rowID from ${table} WHERE ${conceptsFormatted}
		)`;
  }

  __predicate_hideNone(noneKey: string = "safe") {
    const table = new TableRefNode(featureTableName);
    return sql`rowID in (
			SELECT rowID from ${table} WHERE "${noneKey}" == 0
		)`;
  }
}
