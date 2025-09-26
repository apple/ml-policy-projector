/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import {
  coordinator,
  Coordinator,
  DuckDBWASMConnector,
} from "@uwdata/mosaic-core";
import { sql } from "@uwdata/mosaic-sql";

export async function initializeDuckDB() {
  const wasm = new DuckDBWASMConnector({ log: true });
  let coord = new Coordinator(wasm, { cache: false, consolidate: false }); // must turn caching OFF
  coordinator(coord);
  coordinator().databaseConnector(wasm);
}

export async function initializeDatabase(
  parquetURL: string,
  tableName: string
) {
  await coordinator().exec(`DROP TABLE IF EXISTS ${tableName};
        DROP TABLE IF EXISTS ${tableName}_df;
        CREATE TEMP TABLE ${tableName} AS
        SELECT * FROM read_parquet('${parquetURL}');
      `);
  console.log("Table loaded:", tableName, parquetURL);
}

/**
 * @param {string} parquetURL
 */
export async function loadProjectionTable(
  projectionURL: string,
  tableName: string
) {
  let q = sql`
	  CREATE OR REPLACE TABLE ${tableName} AS 
	  SELECT * FROM read_parquet('${projectionURL}')
	`;
  await coordinator().query(q);
  console.log("Island table updated");
}

export async function loadConceptFeatureTable(
  featureURL: string,
  tableName: string
) {
  let q = sql`
	  CREATE OR REPLACE TABLE ${tableName} AS 
	  SELECT * FROM read_parquet('${featureURL}')
	`;
  await coordinator().query(q);
  console.log("Concept feature table loaded");
}

export async function loadReprojection(
  reprojectURL: string,
  tableName: string
) {
  let q = sql`
	CREATE OR REPLACE TABLE "${tableName}" AS 
	SELECT * FROM read_parquet('${reprojectURL}')
  `;
  await coordinator().query(q);
  console.log("Island table updated", tableName);
}
