"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

from flask import Flask, request
from flask_cors import CORS
from os.path import dirname, abspath
import utils
import os
import json
from pyarrow import fs
import uuid
import pandas as pd
import time

# PolicyNav setup
import sys

sys.path.append("../../policy-projector/policy_projector/src")
from policy_projector import PolicyProjector
from concept import Concept
from policy import Policy

NAV = None

app = Flask(__name__)
CORS(app)
static_folder = "../../frontend/build"

rootDir = dirname(abspath(""))
print(rootDir)
local = fs.LocalFileSystem()

DEBUG = True  # Change to False for production
dataDir = "../data/"


# Path to get dataset options
@app.route("/datasets")
def datasets():
    return {"datasets": utils.load_dataset_names(rootDir, dataDir)}


# Path to get a full list of concepts for a given dataset
@app.route("/conceptlist/<dataset>")
def conceptList(dataset):
    data_path = os.path.join(rootDir, dataDir, dataset, dataset + "_concepts.json")
    print("Trying to open data path: ", data_path)
    with app.open_resource(data_path) as f:
        file = f.read()
        jsn = json.loads(file)
        return jsn


# Path to get a full list of policies for a given dataset
@app.route("/policy/<dataset>")
def policyList(dataset):
    data_path = os.path.join(rootDir, dataDir, dataset, dataset + "_policy.json")
    with app.open_resource(data_path) as f:
        file = f.read()
        jsn = json.loads(file)
        return jsn


# Path to get tabular parquet file for a given dataset
@app.route("/tabular/<dataset>.parquet")
async def tabular(dataset):
    print("GETTING TABULAR DATA FOR " + dataset)
    filename = f"{dataset}.parquet"
    path = os.path.join(rootDir, dataDir, dataset, filename)

    # stream parquet file
    def iterfile():
        with local.open_input_stream(path) as stream:
            yield stream.read()

    # update PolicyProjector
    data_path = os.path.join(rootDir, dataDir, dataset)
    df = pd.read_csv(f"{data_path}/{dataset}.csv")
    global NAV  # Reference global var (TODO: refactor)
    NAV = PolicyProjector(
        df,
        id_col="id",
        in_text_col="user_input",
        out_text_col="model_output",
        concept_col="input_harm_cat",
        auto_populate=False,
        base_model_path=None,  # For non-GPU testing
    )

    return app.response_class(iterfile(), mimetype="application/parquet")


# Path to get concept features for a given dataset
@app.route("/features/<dataset>")
async def features(dataset):
    print("GETTING CONCEPT FEATURES FOR " + dataset)
    filename = f"{dataset}_by_concept.parquet"
    path = os.path.join(rootDir, dataDir, dataset, filename)

    # stream parquet file
    def iterfile():
        with local.open_input_stream(path) as stream:
            yield stream.read()

    return app.response_class(iterfile(), mimetype="application/parquet")


# Path to get projection file for a given dataset
@app.route("/projection/<dataset>")
async def projection(dataset: str):
    filename = f"{dataset}_projection.parquet"
    projections_path = os.path.join(rootDir, dataDir, dataset, filename)

    # stream parquet file
    def iterfile():
        with local.open_input_stream(projections_path) as stream:
            yield stream.read()

    return app.response_class(iterfile(), mimetype="application/parquet")


# Path to get re-projection file for a given dataset
@app.route("/reprojection/<dataset>")
async def reprojection(dataset: str):
    filename = f"{dataset}_reproject.parquet"
    projections_path = os.path.join(rootDir, dataDir, dataset, filename)

    # stream parquet file
    def iterfile():
        with local.open_input_stream(projections_path) as stream:
            yield stream.read()

    return app.response_class(iterfile(), mimetype="application/parquet")


# Path to compute reprojection for a given dataset and filters
@app.route("/reproject/<dataset>", methods=["POST"])
async def reproject(dataset: str):
    data = request.get_json()
    concepts = data["concepts"]
    print("reproject!", dataset, concepts)
    data_path = os.path.join(rootDir, dataDir, dataset)
    point_count = utils.reprojectByConcept(data_path, dataset, concepts)
    req_id = uuid.uuid4().hex
    return {"message": "success!", "total_points": point_count, "request_id": req_id}


# Path to add a concept from a provided JSON specification
@app.route("/conceptadd/<dataset>", methods=["POST"])
def add_concept(dataset: str):
    # Parse provided spec
    data = request.get_json()
    concept_spec_str = data["conceptSpec"]
    concept_spec = json.loads(concept_spec_str)

    # Update concept features and concept list
    data_path = os.path.join(rootDir, dataDir, dataset)
    section_name = "Custom Concepts"
    concept = utils.concept_from_spec(concept_spec)
    utils.save_concept(concept, data_path, dataset, section_name)
    return {"message": "success!", "concept_name": concept_spec["name"]}


# Path to add suggested latent concepts for a given dataset
@app.route("/latentConcepts/<dataset>", methods=["POST"])
async def latent_concepts(dataset: str):
    # Parse provided spec
    data = request.get_json()
    concepts = data["concepts"]
    print("get concept suggestions!", dataset, concepts)

    data_path = os.path.join(rootDir, dataDir, dataset)
    global NAV  # Reference global var (TODO: refactor)
    concept_specs = await utils.get_latent_concepts(
        NAV, data_path, dataset, concepts, id_col="id", debug=DEBUG
    )
    data_path = os.path.join(rootDir, dataDir, dataset)

    section_name = "Suggested Concepts"
    for concept_spec in concept_specs:
        concept = utils.concept_from_spec(concept_spec)
        utils.save_concept(concept, data_path, dataset, section_name)
    return {"message": "success!"}


# Path to find similar concepts for the provided dataset and concept
@app.route("/conceptFindSimilar/<dataset>", methods=["POST"])
async def concept_find_similar(dataset: str):
    # Parse provided spec
    data = request.get_json()
    concept = data["concept"]
    limit = data["limit"]

    # Classify examples in the dataset to retrieve more examples
    data_path = os.path.join(rootDir, dataDir, dataset)
    df = pd.read_csv(f"{data_path}/{dataset}.csv")
    concept_spec = utils.concept_to_spec(concept)
    c = Concept(concept_spec)

    pos_score = 1
    score_df = await c.classify(
        df,
        col="model_output",
        in_text_col="user_input",
        id_col="id",
        n=limit,
        sort=False,
        debug=DEBUG,
    )
    if DEBUG:
        score_df = (
            score_df.dropna()
        )  # Handle missing examples since the debug results are fixed
        time.sleep(2)

    score_df_pos = score_df[score_df["score"] == pos_score]
    ex_ids = score_df_pos["id"].tolist()
    return {"message": "success!", "example_ids": ex_ids}


# Path to find matching cases for the provided dataset and policy
@app.route("/policyFindMatches/<dataset>", methods=["POST"])
async def policy_find_matches(dataset: str):
    # Parse provided spec
    data = request.get_json()
    policy = data["policy"]
    limit = data["limit"]

    # Classify examples in the dataset to retrieve more examples
    data_path = os.path.join(rootDir, dataDir, dataset)
    df = pd.read_csv(f"{data_path}/{dataset}.csv")
    policy_spec = utils.policy_to_spec(policy, data_path, dataset)
    p = Policy(policy_spec)

    # Remove examples that are already known to match the concept
    df = df[~df["id"].isin(policy["examples"])]

    pos_score = 1
    score_df = await p.match(
        df,
        col="model_output",
        in_text_col="user_input",
        id_col="id",
        n=limit,
        sort=False,
        debug=DEBUG,
    )
    if DEBUG:
        score_df = (
            score_df.dropna()
        )  # Handle missing examples since the debug results are fixed
        time.sleep(2)

    score_df_pos = score_df[score_df["score"] == pos_score]
    ex_ids = score_df_pos["id"].tolist()
    return {"message": "success!", "example_ids": ex_ids}


# Path to save updated concept metadata
@app.route("/conceptMetadataSave/<dataset>", methods=["POST"])
async def concept_metadata_save(dataset: str):
    data = request.get_json()
    concept = data["concept"]

    # Update concept features and concept list
    data_path = os.path.join(rootDir, dataDir, dataset)
    changed_examples = utils.update_concept(concept, data_path, dataset)
    return {"message": "success!", "changed_examples": changed_examples}


# Path to save updated policy metadata
@app.route("/policyMetadataSave/<dataset>", methods=["POST"])
async def policy_metadata_save(dataset: str):
    data = request.get_json()
    policy = data["policy"]

    data_path = os.path.join(rootDir, dataDir, dataset)
    new_index, new_id, changed_examples = utils.update_policy(
        policy, data_path, dataset
    )
    return {"message": "success!", "changed_examples": changed_examples}


# Path to create concept
@app.route("/conceptCreate/<dataset>", methods=["POST"])
async def concept_create(dataset: str):
    data = request.get_json()
    concept = data["concept"]

    # Update concept features and concept list
    data_path = os.path.join(rootDir, dataDir, dataset)
    section_name = "Custom Concepts"
    utils.save_concept(concept, data_path, dataset, section_name)
    return {"message": "success!"}


# Path to create policy
@app.route("/policyCreate/<dataset>", methods=["POST"])
async def policy_create(dataset: str):
    data = request.get_json()
    policy = data["policy"]

    data_path = os.path.join(rootDir, dataDir, dataset)
    new_index, new_id, _ = utils.update_policy(policy, data_path, dataset)
    return {"message": "success!", "policy_index": new_index, "policy_id": new_id}


# Set default port for localhost to 9001
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9001)
