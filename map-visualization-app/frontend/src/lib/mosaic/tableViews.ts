/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { coordinator } from "@uwdata/mosaic-core";
import { sql } from "@uwdata/mosaic-sql";
import {
  pingDBViews,
  pingDBTable,
  getTableLength,
  getUniqueValuesWithMinFrequency,
} from "./helperQueries";
import {
  baseTableView,
  baseProjectionTableName,
  categoricalTableName,
  mainlandView,
} from "$lib/constants";

const DEBUG = false;
const islandTableName = baseProjectionTableName; // TODO!!!

/**
 * Lists the island names mentioned in this dataset
 */
export async function listIslands() {
  // TODO: limit of 5 is the minimum points we can show in an embedding map
  let islandNames = await getUniqueValuesWithMinFrequency(
    islandTableName,
    "island",
    5
  );
  console.log("This dataset contains islands:", islandNames);
  return islandNames;
}

export async function createIslandDBView(islandName: string) {
  let mapName = islandName;
  let q = sql`
      CREATE OR REPLACE VIEW '${mapName}' AS (
        SELECT * 
        FROM ${baseTableView} 
        WHERE island = '${islandName}'
      )
    `;
  await coordinator().query(q);
  if (DEBUG) console.log("New view created for island", islandName, mapName);
}

export async function createReprojectedView(tableName: string) {
  let viewName = tableName + "_view";
  let q = sql`
	CREATE OR REPLACE VIEW "${viewName}" AS (
	  SELECT * 
	  FROM ${categoricalTableName} 
	  JOIN "${tableName}" ON ("${tableName}".rowID = ${categoricalTableName}.rowID)
	)
  `;
  await coordinator().query(q);

  if (DEBUG) {
    console.log("Updated reprojected view table", viewName);
    let count = await getTableLength(viewName);
    let table_count = await getTableLength(tableName);
    console.log(
      "New map view length",
      count,
      "from a table of",
      table_count,
      tableName,
      viewName
    );
  }
  return viewName;
}

export async function createBaseTableView() {
  let q = sql`
      CREATE OR REPLACE VIEW ${baseTableView} AS (
        SELECT * 
        FROM ${categoricalTableName} 
        JOIN ${islandTableName} ON (${islandTableName}.rowID = ${categoricalTableName}.rowID)
      )
    `;
  await coordinator().query(q);
  if (DEBUG) console.log("Updated base view table", baseTableView);
}

/* Debug helper function */
/**
 * @param {string[]} islands
 */
export async function debugTablesAndViews(islands = []) {
  pingDBViews();
  pingDBTable(islandTableName);
  pingDBTable(categoricalTableName);
  pingDBTable(baseTableView);

  let islandCheck = await getTableLength(islandTableName);
  let baseTableCheck = await getTableLength(baseTableView);
  let mainlandCheck = await getTableLength(mainlandView);

  console.log("Island table has length of:", islandCheck);
  console.log("Base table has length of:", baseTableCheck);
  console.log("Mainland has length of:", mainlandCheck);

  islands.forEach(async (islandName) => {
    let check = await getTableLength(islandName);
    console.log("Island " + islandName + " has length of:", check);
  });
}
