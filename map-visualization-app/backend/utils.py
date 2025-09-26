"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

import os
import json
import pandas as pd
import numpy as np
from umap import UMAP
from typing import Dict, Optional, List


def load_dataset_names(rootDir: str, dataDir: str) -> list:
    data_path = os.path.join(rootDir, f"{dataDir}/")
    dir_list = [
        directory
        for directory in os.listdir(data_path)
        if os.path.isdir(data_path + directory) and not directory.startswith(".")
    ]
    return dir_list


# Adds a concept to the one-hot feature table
def add_to_concept_features(
    concept: Dict, data_path: str, dataset: str, is_new_concept: bool = True
):
    df_feat = pd.read_parquet(f"{data_path}/{dataset}_by_concept.parquet")
    df = pd.read_csv(f"{data_path}/{dataset}.csv")
    concept_name = concept["name"]

    if is_new_concept:
        # Add column for new concept; fill with 0s
        default_score = 0
        df_feat = df_feat.assign(**{concept_name: default_score})

    # For each example, get its row ID based on index in original df
    ex_ids = concept["examples"]
    row_ids = df[df["id"].isin(ex_ids)].index.tolist()

    # For those rows in df_feat, set label to 1
    df_feat.loc[row_ids, concept_name] = 1
    return df_feat


# Gets the JSON spec for the specified concept
def concept_to_spec(concept: Dict):
    spec = {
        "name": concept["name"],
        "description": concept["definition"],
        "examples": concept["examples"],
        "fixes": None,
        "id": None,
    }
    return spec


def get_concept_by_name(concept_name: str, data_path: str, dataset: str):
    with open(f"{data_path}/{dataset}_concepts.json", "rb") as f:
        concepts = json.load(f)

    # Retrieve concept by name
    for i, concept_section in enumerate(concepts):
        for j, existing_concept in enumerate(concept_section["concepts"]):
            if existing_concept["name"] == concept_name:
                return existing_concept

    return None


# Gets the JSON spec for the specified policy
def policy_to_spec(policy: Dict, data_path: str, dataset: str):
    # Create concept specs
    policy_concepts = [
        get_concept_by_name(c_name, data_path, dataset) for c_name in policy["if"]
    ]
    concept_specs = [concept_to_spec(c) for c in policy_concepts if c is not None]
    spec = {
        "name": policy["name"],
        "description": policy["description"],
        "examples": policy["examples"],
        "if": concept_specs,
        "id": policy["id"],
        "then": policy["then"],
    }
    return spec


# Converts a concept spec JSON to a concept dictionary (for back-compatibility)
def concept_from_spec(c_spec: Dict):
    ex_ids = [ex["id"] for ex in c_spec["examples"]]
    new_concept = {
        "definition": c_spec["description"],
        "examples": ex_ids,
        "name": c_spec["name"],
        "display_name": c_spec["name"],
    }
    return new_concept


# Adds a concept to the concept dictionary
def add_to_concept_json(concept: Dict, data_path: str, dataset: str, section_name: str):
    with open(f"{data_path}/{dataset}_concepts.json", "rb") as f:
        concepts = json.load(f)

    # Add to specified concept section
    for concept_section in concepts:
        if concept_section["name"] == section_name:
            # Add to existing section
            concept_section["concepts"].append(concept)
            return concepts

    # Create new section
    new_section = {
        "concepts": [concept],
        "definition": "",
        "name": section_name,
    }
    concepts.append(new_section)
    return concepts


# Wrapper function that updates concept features and JSON to save a new concept spec
def save_concept(concept: Dict, data_path: str, dataset: str, section_name: str):
    df_feat = add_to_concept_features(concept, data_path, dataset, is_new_concept=True)
    concepts = add_to_concept_json(concept, data_path, dataset, section_name)
    save_concept_results(df_feat, concepts, data_path, dataset)


# Updates a concept in the concept dictionary
def update_concept_json(updated_concept: Dict, data_path: str, dataset: str):
    with open(f"{data_path}/{dataset}_concepts.json", "rb") as f:
        concepts = json.load(f)

    # Remove computed fields
    updated_concept.pop("count", None)
    updated_concept.pop("centroid", None)

    # Update concept entry
    changed_examples = False
    for i, concept_section in enumerate(concepts):
        for j, existing_concept in enumerate(concept_section["concepts"]):
            if existing_concept["name"] == updated_concept["name"]:
                existing_examples = existing_concept["examples"]
                updated_examples = updated_concept["examples"]
                if existing_examples != updated_examples:
                    changed_examples = True
                concepts[i]["concepts"][j] = updated_concept
                return concepts, changed_examples

    return concepts, changed_examples


# Updates the specified concept
def update_concept(concept: Dict, data_path: str, dataset: str):
    df_feat = None
    concepts, changed_examples = update_concept_json(concept, data_path, dataset)
    if changed_examples:
        df_feat = add_to_concept_features(
            concept, data_path, dataset, is_new_concept=False
        )
    save_concept_results(df_feat, concepts, data_path, dataset)
    return changed_examples


# Updates the specified policy
def update_policy(policy: Dict, data_path: str, dataset: str):
    policies, index, cur_id, changed_examples = update_policy_json(
        policy, data_path, dataset
    )
    if changed_examples:
        # Update concepts accordingly so manual example additions appear on map
        new_examples = policy["examples"]
        policy_concepts = [
            get_concept_by_name(c_name, data_path, dataset) for c_name in policy["if"]
        ]
        for c in policy_concepts:
            # Add examples to each concept and update metadata
            c_new_ex = [ex_id for ex_id in new_examples if ex_id not in c["examples"]]
            c["examples"].extend(c_new_ex)
            update_concept(c, data_path, dataset)
    save_policy_results(policies, data_path, dataset)
    return index, cur_id, changed_examples


# Updates a policy in the policy dictionary
def update_policy_json(updated_policy: Dict, data_path: str, dataset: str):
    with open(f"{data_path}/{dataset}_policy.json", "rb") as f:
        policies = json.load(f)

    # Remove computed fields
    updated_policy.pop("count", None)
    updated_policy.pop("centroid", None)

    # Update policy entry
    changed_examples = False
    for i, existing_policy in enumerate(policies):
        if existing_policy["id"] == updated_policy["id"]:
            existing_examples = existing_policy["examples"]
            updated_examples = updated_policy["examples"]
            if existing_examples != updated_examples:
                changed_examples = True
            policies[i] = updated_policy
            index = updated_policy["index"]
            cur_id = updated_policy["id"]
            return policies, index, cur_id, changed_examples

    # Otherwise: add since not already present
    index = len(policies)
    cur_id = f"p{index + 1}"
    updated_policy["index"] = index
    updated_policy["id"] = cur_id
    policies.append(updated_policy)
    changed_examples = True

    return policies, index, cur_id, changed_examples


def get_existing_concepts(data_path: str, dataset: str):
    # Fetch list of names of all existing concepts
    with open(f"{data_path}/{dataset}_concepts.json", "rb") as f:
        concepts = json.load(f)

    existing_concept_names = []
    for concept_section in concepts:
        for existing_concept in concept_section["concepts"]:
            existing_concept_names.append(existing_concept["name"])
    return existing_concept_names


def filterByRowID(df_path, rowIDs, id_col):
    # Get example ID from row IDs
    df = pd.read_parquet(df_path)
    df = df[df.index.isin(rowIDs)]
    return df[id_col].tolist()


# Gets suggestions for latent concepts using the PolicyProjector library
async def get_latent_concepts(
    nav, data_path, dataset, concept_filters, id_col, debug: bool
):
    # Apply concept filters (if provided)
    if len(concept_filters) > 0:
        concept_path = f"{data_path}/{dataset}_by_concept.parquet"
        rowIDs = filterByConcept(concept_path, concept_filters)
        df_path = f"{data_path}/{dataset}.parquet"
        ex_ids = filterByRowID(df_path, rowIDs, id_col=id_col)
    else:
        ex_ids = []

    # Get existing concepts
    existing_concepts = get_existing_concepts(data_path, dataset)

    # Request concept suggestions
    _, suggested_specs = await nav.suggest_concepts(
        filter_ids=ex_ids,
        existing_concepts=existing_concepts,
        limit=100,
        interactive=False,
        debug=debug,
    )
    return suggested_specs


# Saves the provided feature table and concept dictionary to file
def save_concept_results(
    df_feat: Optional[pd.DataFrame],
    concepts: Optional[Dict],
    data_path: str,
    dataset: str,
):
    if df_feat is not None:
        df_feat.to_parquet(f"{data_path}/{dataset}_by_concept.parquet")
    if concepts is not None:
        with open(f"{data_path}/{dataset}_concepts.json", "w") as f:
            json.dump(concepts, f, indent=2)


# Saves the provided policy dictionary to file
def save_policy_results(policies: Dict, data_path: str, dataset: str):
    with open(f"{data_path}/{dataset}_policy.json", "w") as f:
        json.dump(policies, f, indent=2)


# given a set of concepts, reproject filtered data
def reprojectByConcept(data_path: str, dataset: str, concepts: list):
    concept_path = f"{data_path}/{dataset}_by_concept.parquet"
    embedding_path = f"{data_path}/{dataset}_embeddings.npy"
    reproject_path = f"{data_path}/{dataset}_reproject.parquet"
    rowIds = filterByConcept(concept_path, concepts)
    reproject(embedding_path, reproject_path, rowIds)
    return len(rowIds)


# Gets the row ids that match a set of concepts
def filterByConcept(CONCEPT_PATH: str, CONCEPTS: list):
    df = pd.read_parquet(CONCEPT_PATH)
    return list(df[df[CONCEPTS].astype(bool).all(axis="columns")].index)


# Given row ids, reproject a subset of the data
def reproject(EMBED_PATH: str, REPROJECT_PATH: str, rowIDs: list):
    embeddings = np.load(EMBED_PATH)
    embed_rows = embeddings[rowIDs, :]
    reducer = UMAP(metric="cosine")
    embeddings_2d = reducer.fit_transform(embed_rows)
    xs = embeddings_2d[:, 0].astype(float)
    ys = embeddings_2d[:, 1].astype(float)
    df_proj = pd.DataFrame(data={"x": xs, "y": ys}, index=rowIDs)
    df_proj["rowID"] = df_proj.index.astype(int)
    df_proj.to_parquet(REPROJECT_PATH)
