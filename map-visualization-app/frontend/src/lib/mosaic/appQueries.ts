/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { type ConceptGroup, type Policy } from "$lib/types";
import { coordinator } from "@uwdata/mosaic-core";
import { TableRefNode } from "@uwdata/mosaic-sql";
import {
  baseProjectionTableName,
  featureTableName,
  categoricalTableName,
} from "$lib/constants";
import { type Selection as MosaicSelection } from "@uwdata/mosaic-core";

const DEBUG = true;

export async function getRowsByConcepts(conceptNames: string[]) {
  let r;
  let count;
  let catTable = new TableRefNode(categoricalTableName);
  let featTable = new TableRefNode(featureTableName);
  if (conceptNames.length > 0) {
    // Run query to retrieve matching examples
    let conceptFilters = conceptNames.map((c) => `"${c}" == 1`);
    let conceptsFormatted = conceptFilters.join(" AND ");
    r = await coordinator().query(
      `SELECT user_input as in_text, model_output as out_text, input_harm_cat as harm, "id"
            FROM ${catTable}
            WHERE rowID IN (
                SELECT rowID 
                FROM ${featTable}
                WHERE ${conceptsFormatted}
            )`
    );
    let r_count = await coordinator().query(
      `SELECT COUNT(*) as count
            FROM ${catTable}
            WHERE rowID IN (
                SELECT rowID 
                FROM ${featTable}
                WHERE ${conceptsFormatted}
            )`
    );
    let bigNumber = r_count.get(0).count;
    count = Number(bigNumber);
  } else {
    // Run query to view all examples (current limit of 500)
    const limit = 500;
    r = await coordinator().query(
      `SELECT user_input as in_text, model_output as out_text, input_harm_cat as harm, "id"
            FROM ${catTable}
            limit ${limit}`
    );
    let r_count = await coordinator().query(
      `SELECT COUNT(*) as count
            FROM ${catTable}`
    );
    let bigNumber = r_count.get(0).count;
    count = Number(bigNumber);
  }

  let ids = r.getChild("id").toArray();
  let in_texts = r.getChild("in_text").toArray();
  let out_texts = r.getChild("out_text").toArray();
  let harms = r.getChild("harm").toArray();
  let rows = in_texts.map(function (in_text: string, i: number) {
    return [ids[i], in_text, out_texts[i], harms[i]];
  });
  return { rows: rows, count: count };
}

export async function getRowsByExampleIds(exampleIDs: string[]) {
  let exampleIDsFormatted = "'" + exampleIDs.join("','") + "'";
  let table = new TableRefNode(categoricalTableName);
  let r = await coordinator().query(
    `SELECT user_input as in_text, model_output as out_text, "id"
        FROM ${table}
        WHERE "id" IN (${exampleIDsFormatted})`
  );

  let ids = r.getChild("id").toArray();
  let in_texts = r.getChild("in_text").toArray();
  let out_texts = r.getChild("out_text").toArray();
  let rows = in_texts.map(function (in_text: string, i: number) {
    return [ids[i], in_text, out_texts[i]];
  });
  return rows;
}

export async function getRowsByRangeSelection(
  selection: typeof MosaicSelection,
  projectionTable: string
) {
  let predicate = selection.active?.predicate.toString();
  if (DEBUG) console.log("Selection predicate is", predicate);
  let table = new TableRefNode(projectionTable);
  let r = await coordinator().query(
    `SELECT user_input as in_text, model_output as out_text, "id"
        FROM ${table}
        WHERE ${predicate}`
  );

  let ids = r.getChild("id").toArray();
  let in_texts = r.getChild("in_text").toArray();
  let out_texts = r.getChild("out_text").toArray();
  let rows = in_texts.map(function (in_text: string, i: number) {
    return [ids[i], in_text, out_texts[i]];
  });
  return rows;
}

export async function updateCentroids(
  concepts: ConceptGroup[],
  filter: string = "",
  projectionTable: string = baseProjectionTableName
) {
  if (DEBUG)
    console.log("Recomputing centroids!", concepts, filter, projectionTable);
  await Promise.all(
    concepts?.map(async (group) => {
      // get details for concepts
      await Promise.all(
        group.concepts?.map(async (c) => {
          if (c.count ?? 0 > 0)
            c.centroid = await getMedianPos(c.name, filter, projectionTable);
        })
      );
      // get details for "none" concept
      if (group.none?.name) {
        if (group.none?.count ?? 0 > 0)
          group.none.centroid = await getMedianPos(
            group.none.name,
            filter,
            projectionTable
          );
      }
    })
  );

  return concepts;
}

export async function updatePolicyCentroids(
  policies: Policy[],
  filter: string = "",
  projectionTable: string = baseProjectionTableName
) {
  if (DEBUG)
    console.log(
      "Recomputing policy centroids!",
      policies,
      filter,
      projectionTable
    );
  await Promise.all(
    policies?.map(async (p) => {
      if (p.count ?? 0 > 0)
        p.centroid = await getPolicyMedianPos(p, filter, projectionTable);
    })
  );

  return policies;
}

export async function sumColumn(c: string, filter: string): Promise<number> {
  let table = new TableRefNode(featureTableName);
  let r = await coordinator().query(
    `SELECT SUM("${c}") as count FROM ${table}${filter ? `WHERE ${filter}` : ""}`
  );
  let bigNumber = r.getChild("count").toArray()[0];
  return Number(bigNumber);
}

export async function sumPolicyColumns(
  p: Policy,
  filter: string
): Promise<number> {
  let conceptNames = p.if;
  if (conceptNames.length == 0) return 0;
  let conceptFilters = conceptNames.map((c) => `"${c}" == 1`);
  let conceptsFormatted = conceptFilters.join(" AND ");
  let table = new TableRefNode(featureTableName);
  let r = await coordinator().query(
    `SELECT COUNT(rowID) as count
        FROM ${table}
		WHERE ${conceptsFormatted}
        ${filter ? ` AND ${filter}` : ""}`
  );
  let bigNumber = r.getChild("count").toArray()[0];
  return Number(bigNumber);
}

export async function getMedianPos(
  column: string,
  filter: string,
  projectionTable: string
) {
  let projTable = new TableRefNode(projectionTable);
  let featTable = new TableRefNode(featureTableName);
  let r = await coordinator().query(
    `SELECT MEDIAN("x") as medianX, MEDIAN("y") as medianY 
        FROM ${projTable}
        WHERE rowID in (
            SELECT rowID from ${featTable} WHERE "${column}" == 1
        )${filter ? ` AND ${filter}` : ""}`
  );
  let x = r.getChild("medianX").toArray()[0];
  let y = r.getChild("medianY").toArray()[0];
  return { x, y };
}

export async function getPolicyMedianPos(
  p: Policy,
  filter: string,
  projectionTable: string
) {
  let conceptNames = p.if;
  if (conceptNames.length == 0) return undefined;
  let conceptFilters = conceptNames.map((c) => `"${c}" == 1`);
  let conceptsFormatted = conceptFilters.join(" AND ");
  let projTable = new TableRefNode(projectionTable);
  let featTable = new TableRefNode(featureTableName);
  let r = await coordinator().query(
    `SELECT MEDIAN("x") as medianX, MEDIAN("y") as medianY 
        FROM ${projTable}
        WHERE rowID in (
            SELECT rowID from ${featTable} 
			WHERE ${conceptsFormatted}
        )${filter ? ` AND ${filter}` : ""}`
  );
  let x = r.getChild("medianX").toArray()[0];
  let y = r.getChild("medianY").toArray()[0];
  return { x, y };
}
