/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { coordinator } from "@uwdata/mosaic-core";
import { sql, TableRefNode } from "@uwdata/mosaic-sql";

export const pingDBViews = async () => {
  let q = sql`
    SELECT * FROM duckdb_views
      `;
  let r = await coordinator().query(q);
  console.log(
    "Current Database Views ",
    // @ts-ignore
    r.toArray().map((value) => value.toJSON())
  );
};

export const pingDBTable = async (tableName: string) => {
  let q = sql`SUMMARIZE ${tableName}`;
  let r = await coordinator().query(q);
  console.log(
    "Current Tables",
    // @ts-ignore
    r.toArray().map((value) => value.toJSON())
  );
};

export const getTableLength = async (
  tableName: string,
  filter: string = ""
) => {
  let r = await coordinator().query(
    `SELECT COUNT(*) AS count FROM '${tableName}'${filter ? ` WHERE ${filter}` : ""}`
  );
  let bigNumber = r.get(0).count; // may be a big int or big number type
  return Number(bigNumber);
};

export const getPointByID = async (
  tableName: string,
  id_column: string,
  id_value: any
) => {
  let q = sql`
        SELECT * FROM '${tableName}'
        WHERE ${id_column}='${id_value}'
        LIMIT 1;
      `;
  let r = await coordinator().query(q);
  let jsn = r.get(0).toJSON();

  // convert any BigInt to string
  Object.keys(jsn).forEach((key) => {
    if (typeof jsn[key] == "bigint") jsn[key] = jsn[key].toString();
  });
  return jsn;
};

export async function getUniqueValues(tableName: string, columnName: string) {
  let table = new TableRefNode(tableName);
  let r = await coordinator().query(
    `SELECT DISTINCT "${columnName}" FROM ${table}`
  );
  return r.getChild(columnName).toArray();
}

export async function getUniqueValuesWithMinFrequency(
  tableName: string,
  columnName: string,
  minCount: number
) {
  let table = new TableRefNode(tableName);
  let r = await coordinator().query(
    `SELECT "${columnName}", COUNT(*) as count 
    FROM ${table}
    GROUP BY "${columnName}"
    ORDER BY count DESC`
  );

  let unique = r.getChild(columnName).toArray();
  let counts = r.getChild("count").toArray();
  let passes: { [key: string]: number } = {};

  unique.forEach((value: string, index: number) => {
    let count = Number(counts[index]);
    if (count > minCount) passes[value] = count;
  });

  return passes;
}
