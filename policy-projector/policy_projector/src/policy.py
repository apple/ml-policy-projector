"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# Policy
import pandas as pd
import json

import util
import prompts as p
from dataset import Dataset
from concept import Concept


class Policy:

    # Policy setup
    # spec (Dict): specification with policy details
    def __init__(self, spec):
        # TODO: validate policy spec
        # Core policy details
        self.name = spec["name"]
        if "id" in spec:
            self.id = spec["id"]
        else:
            # TODO: suggest an id if it's not provided
            self.id = spec["name"]
        self.description = spec["description"]

        # If-conditions
        self.if_conditions = spec["if"]  # Concept specs
        self.if_concepts = [Concept(c_spec) for c_spec in self.if_conditions]
        self.if_concept_names = [c.name for c in self.if_concepts]

        # Then-actions
        if "then" in spec:
            self.then_concepts = spec["then"]
        else:
            self.then_actions = None

        # Examples
        self.examples = spec["examples"]  # IDs of positive examples
        self.fixes = spec["fixes"] if "fixes" in spec else []
        # TODO: update referenced concepts to also reference this policy

    def to_spec(self, include_examples: bool):
        spec = {
            "name": self.name,
            "id": self.id,
            "description": self.description,
            "if": self.if_conditions,
            "then": self.then_actions,
            "examples": self.examples if include_examples else [],
        }
        spec_str = json.dumps(spec, indent=2)
        print(spec_str)

    # View and edit policy details
    # - df (pd.DataFrame): dataframe on which policy is based
    # - id_col (str): name of df column with unique IDs
    # - in_text_col (str): name of df column with input text
    # - out_text_col (str): name of df column with output text
    # - show_fixes (bool): whether to show examples joined with their paired fixes (default: False)
    def view(self, df, id_col, in_text_col, out_text_col, show_fixes: bool = False):
        # TODO: add back support for show_fixes to pair examples with fixes in view
        dataset = util.ex_ids_to_dataset(
            self.examples, df, id_col, in_text_col, out_text_col, score=1, source=None
        )
        text_cols = dataset.text_cols

        from __init__ import TableWidget

        w = TableWidget(
            obj=self,
            obj_type="Policy",
            dataset=dataset,
            cols_to_show=dataset.cols,
            text_cols=text_cols,
            editable_cols=[],
        )
        return w

    # Classifies whether the provided data matches the policy
    # In other words, checks the "IF-conditions" for each item
    # - df (pd.DataFrame): dataframe on which to run the classification
    # - col (str): name of the text column in the dataframe to classify
    # - in_text_col (str): name of df column with input text
    # - id_col (str): name of df column with unique IDs
    # - n (int): maximum number of df examples to classify
    # - sort (bool): whether to sort results with positives at the top
    # - show_widget (bool): whether to show the notebook widget
    async def match(
        self,
        df: pd.DataFrame,
        col: str,
        in_text_col: str,
        id_col: str,
        n: int = 20,
        sort: bool = True,
        debug: bool = False,
        show_widget: bool = False,
    ):
        # Filter to examples in df where all if-conditions are true
        # Classify all provided examples (use existing score if available)
        if n is None:
            limit = len(df)
        else:
            limit = min(len(df), n)
        cur_df = df.sample(n=limit)
        orig_df = cur_df.copy()
        cur_df["score"] = 1

        # Classify each concept and keep running tally of scores
        for concept in self.if_concepts:
            score_df = await concept.classify(
                orig_df,
                col=col,
                in_text_col=in_text_col,
                id_col=id_col,
                n=None,
                sort=False,
                debug=debug,
            )
            score_df[concept.name] = score_df["score"]
            score_df = score_df[[col, concept.name]]

            # Merge concept score with existing df
            cur_df = cur_df.merge(score_df, on=col)

            # Update score column with new concept scores
            cur_df = cur_df.fillna(0)
            cur_df = cur_df.astype({"score": int, concept.name: int})  # Cast types
            cur_df["score"] = cur_df["score"] & cur_df[concept.name]
            # TODO: handle other boolean operators. handle NaN values.

        if sort:
            cur_df = cur_df.sort_values(by=["score"], ascending=False)

        cur_df = cur_df.assign(**{"source": "auto"})

        if show_widget:
            from __init__ import TableWidget

            examples = Dataset(
                df=cur_df,
                id_col=id_col,
                in_text_col=in_text_col,
                out_text_col=col,
                score_col="score",
                source_col="source",
            )
            w = TableWidget(
                obj=self,
                obj_type="Policy",
                dataset=examples,
                cols_to_show=examples.cols,
                text_cols=examples.text_cols,
                score_col="score",
                edit_type="Example",
                editable_cols=["score"],
            )
            return w

        return cur_df

    # Modifies the provided data to behave in line with the policy
    # In other words, applies the "THEN-actions" to each item
    # - df (pd.DataFrame): dataframe on which to run the policy generation
    # - in_text_col (str): name of the input text column in the dataframe to apply generation
    # - base_model (BaseModel*): the base model to use for training the intervention
    # - n (int): maximum number of df examples with which to perform generation
    # - n_epochs (int): number of epochs for intervention training
    # - n_trials (int): number of independent generations to produce
    def act(
        self,
        df: pd.DataFrame,
        in_text_col: str,
        base_model,
        n: int = 10,
        n_epochs: int = 30,
        n_trials: int = 3,
    ):
        # TODO: handle if then-condition is an example, not a concept

        # Route to the specified concept
        then_concept = self.then_concepts[0]  # TODO: handle chaining of multiple
        df_gen = then_concept.gen(df, in_text_col, base_model, n, n_epochs, n_trials)
        return df_gen
