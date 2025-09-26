/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import TableView from "./components/TableView.svelte";
import { mount } from "svelte";

export function render({ model, el }) {
  let wv = mount(TableView, { target: el, props: { model, el } });
  return () => wv.$destroy();
}
