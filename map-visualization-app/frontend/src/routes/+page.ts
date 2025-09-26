/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import type { PageLoad } from './$types';
import { fetchDatasetOptions } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	await fetchDatasetOptions(fetch);
};
