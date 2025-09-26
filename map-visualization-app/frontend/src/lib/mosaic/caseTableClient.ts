/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { MosaicClient } from "@uwdata/mosaic-core";
import { type ExampleRow } from "$lib/types";
import {
  caseTableRows,
  caseTableHeaders,
  mapSelectionClauses,
  mapTable,
} from "$lib/store";
import { Query, desc } from "@uwdata/mosaic-sql";
import { baseProjectionTableName, paginationLimit } from "$lib/constants";

// adapted from https://github.com/uwdata/mosaic/blob/main/packages/inputs/src/Table.js
export class CaseTableClient extends MosaicClient {
  constructor(ops: { filterBy: Selection; as: Selection; fromTable: string }) {
    super(ops.filterBy);
    this.selection = ops.as;
    this.from = ops.fromTable;
    this.columns = ["*"];

    // pagination
    this.offset = 0;
    this.limit = paginationLimit;
    //this.pending = false;

    // table sorting
    this.sortColumn = null;
    this.sortDesc = false;

    // projection table
    this.projectionTable = baseProjectionTableName;
    mapTable.subscribe((value) => {
      if (value) this.projectionTable = value;
    });

    //map selection
    mapSelectionClauses.subscribe((value) => {
      if (value) {
        this.selection.update(value);
      }
    });
  }

  query(filter: []) {
    const { limit, offset, sortColumn, sortDesc } = this;
    return Query.from(this.projectionTable)
      .select(["*"])
      .where(filter)
      .orderby(sortColumn ? (sortDesc ? desc(sortColumn) : sortColumn) : [])
      .limit(limit)
      .offset(offset);
  }

  queryResult(data: any) {
    if (!this.pending) {
      // data is not from an internal request, so reset table
      this.loaded = false;
      this.offset = 0;
    }
    let headers = data?.schema.fields.map((field: any) => field.name);
    caseTableHeaders.set(headers);

    let rows: ExampleRow[] = [];
    data.toArray().forEach((row: any) => {
      // format all data as a string for now
      rows.push(Object.values(row).map((s: any) => s?.toString() ?? ""));
    });
    caseTableRows.set(rows);

    if (rows.length < this.limit) {
      // data table has been fully loaded
      this.loaded = true;
    }

    //this.pending = false;
    return this;
  }

  requestMoreData() {
    this.pending = true;
    this.offset += this.limit;

    // request next data batch
    const query = this.query(this.filterBy?.predicate(this));
    this.requestQuery(query);
  }
}
