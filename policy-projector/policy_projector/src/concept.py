"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# Concept
import numpy as np
import pandas as pd
import json
from typing import Optional
import random
import torch
import time

import llm
import util
import prompts as p
from dataset import Dataset


class Concept:

    # Concept setup
    # spec (Dict): specification with concept details
    # labeled (bool): whether the data has already been labeled for this concept
    # label_col (str): column name with labels (if available)
    def __init__(self, spec, labeled=False, label_col=None):
        # TODO: validate concept spec
        # Core concept details
        self.name = spec["name"]
        if "id" in spec:
            self.id = spec["id"]
        else:
            # TODO: suggest an id if it's not provided
            self.id = spec["name"]
        self.description = spec["description"]

        # Examples
        # TODO: validate provided examples
        self.examples = spec["examples"]  # IDs of positive examples
        self.fixes = spec["fixes"] if "fixes" in spec else []
        self.labeled = labeled
        self.label_col = label_col

        # Policies that reference this concept
        self.policies = []

        # Intervention (to be trained)
        self.interv = None

    def to_spec(self, include_examples: bool, return_dict: bool = False):
        spec = {
            "name": self.name,
            "id": self.id,
            "description": self.description,
            "examples": self.examples if include_examples else [],
        }
        spec_str = json.dumps(spec, indent=2)
        print(spec_str)
        if return_dict:
            return spec

    # View and edit concept details
    # - df (pd.DataFrame): dataframe on which concept is based
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
            obj_type="Concept",
            dataset=dataset,
            cols_to_show=dataset.cols,
            text_cols=text_cols,
            editable_cols=[],
        )
        return w

    # Helper to parse bucketed score from LLM response to numerical result
    def __parse_bucketed_score(self, x, nan_score=np.nan):
        answer_scores = {
            "A": 1,
            "B": 0,
        }
        if len(x) > 1:
            x = x[0]
        if x not in answer_scores.keys():
            return nan_score
        return answer_scores[x]

    # Run classification prompt for the concept
    # - df (pd.DataFrame): dataframe on which to run the concept prompt
    # - col (str): name of the text column in the dataframe for which to classify the concept
    # - id_col (str): name of id column in dataframe
    # - limit (int): maximum number of df examples to classify
    # - n_pos_examples (int): number of
    async def __run_concept_prompt(
        self,
        df: pd.DataFrame,
        col: str,
        id_col: str,
        limit: Optional[int] = None,
        n_pos_examples: int = 3,
    ):
        # Remove examples that are already known to match the concept
        cur_df = df[~df["id"].isin(self.examples)]

        if limit is not None:
            limit = min(len(cur_df), limit)
            cur_df = cur_df.sample(n=limit)  # Take random sample
        else:
            cur_df = cur_df.copy()

        # Prepare prompt arguments
        examples = cur_df[col].tolist()
        criteria = f"{self.name}: {self.description}"
        pos_example_ids = self.examples
        if len(pos_example_ids) > 0:
            # Prepare prompt with few-shot examples
            if len(pos_example_ids) > n_pos_examples:
                pos_example_ids = random.sample(pos_example_ids, n_pos_examples)
            pos_examples = [
                util.get_ex_col(df, ex_id, id_col, col) for ex_id in pos_example_ids
            ]
            prompt_template = p.unit_test_prompt_v3
            arg_dicts = [
                {"ex": ex, "criteria": criteria, "concept_examples": pos_examples}
                for ex in examples
            ]
        else:
            # Prompt without few-shot examples
            prompt_template = p.unit_test_prompt_v2
            arg_dicts = [{"ex": ex, "criteria": criteria} for ex in examples]

        # Run prompt
        res, _ = await llm.multi_query_gpt_wrapper(
            prompt_template,
            arg_dicts,
            MODEL,
        )
        # TODO: re-run in cases of failure up to n times

        # Process results
        rows = []
        for arg_dict, res in zip(arg_dicts, res):
            res_parsed = llm.json_load(res, "pattern_result")
            if res_parsed is not None:
                score = self.__parse_bucketed_score(res_parsed["answer"])
                rationale = res_parsed["rationale"]
            else:
                score = None
                rationale = None
            row = [arg_dict["ex"], score, rationale]
            rows.append(row)

        scores_df = pd.DataFrame(rows, columns=[col, "score", "rationale"])
        return scores_df

    # Classifies whether the provided data matches the concept
    # - df_in (pd.DataFrame): dataframe on which to run the concept prompt
    # - col (str): name of the text column in the dataframe for which to classify the concept
    # - in_text_col (str): name of df column with input text
    # - id_col (str): name of df column with unique IDs
    # - n (int): maximum number of df examples to classify
    # - sort (bool): whether to sort results with positives at the top
    # - show_widget (bool): whether to show the notebook widget
    async def classify(
        self,
        df_in: pd.DataFrame,
        col: str,
        in_text_col: str,
        id_col: str,
        n: int = 20,
        sort: bool = True,
        debug: bool = False,
        show_widget: bool = False,
    ):
        df = df_in.copy()
        if self.labeled:
            # Retrieve existing labels
            def get_score(row):
                if row[self.label_col] == self.name:
                    return 1
                return 0

            rows = [[row[col], get_score(row), None] for i, row in df.iterrows()]
            score_df = pd.DataFrame(rows, columns=[col, "score", "rationale"])
        else:
            if debug:
                # Fetch cached labels for testing
                import cached.concept_classify as cache

                score_rows = cache.score_rows
                score_df = pd.DataFrame(score_rows)
            else:
                # Fetch new labels
                score_df = await self.__run_concept_prompt(
                    df,
                    col,
                    id_col,
                    limit=n,
                )

        # Join with original df
        score_df = score_df.merge(df, on=col, how="left")
        if sort:
            score_df = score_df.sort_values(by=["score"], ascending=False)

        score_df = score_df.assign(**{"source": "auto"})

        if show_widget:
            from __init__ import TableWidget

            score_examples = Dataset(
                df=score_df,
                id_col=id_col,
                in_text_col=in_text_col,
                out_text_col=col,
                score_col="score",
                source_col="source",
                cols=[in_text_col, col, "score", "rationale", id_col, "source"],
            )
            w = TableWidget(
                obj=self,
                obj_type="Concept",
                dataset=score_examples,
                cols_to_show=score_examples.cols,
                text_cols=score_examples.text_cols + ["rationale"],
                score_col="score",
                edit_type="Example",
                editable_cols=["score"],
            )
            return w

        return score_df

    # Post-processes the steered generations
    # - df_in (pd.DataFrame): dataframe with generations
    # - col (str): df column name with steered generation text
    def __parse_steered_gen(self, df_in: pd.DataFrame, col: str):
        df = df_in.copy()

        def parse_gen(x):
            x = x.split("\n")[0]  # Take text before newline
            return x

        df[col] = [parse_gen(x) for x in df[col].tolist()]
        return df

    def get_example_fix_pairs(self):
        # Match examples and fixes datasets; take inner join
        df_merged = Dataset.join(
            d1=self.examples,
            d2=self.fixes,
            cols1=None,
            cols2=[self.fixes.id_col, self.fixes.out_text_col],
        )
        in_text_col = self.examples.in_text_col
        orig_col = f"{self.examples.out_text_col}_x"
        fix_col = f"{self.examples.out_text_col}_y"
        # Prepare (input text, fix) tuples
        train_pairs = [
            (row[in_text_col], row[fix_col]) for _, row in df_merged.iterrows()
        ]
        return train_pairs

    def format_reft_input(self, df_in, in_col, orig_out_col):
        template = """
Please summarize the following text into a one-sentence text message summary.
    
ORIGINAL TEXT: 
{in_text}

DRAFT VERSION:
{orig_out_text}

Please only return the single one-sentence summary.
"""
        df = df_in.copy()
        df[in_col] = [
            template.format(in_text=row[in_col], orig_out_text=row[orig_out_col])
            for _, row in df.iterrows()
        ]
        return df

    # Modifies the provided test data to express the concept from training data
    # - train_df (pd.DataFrame): dataframe on which to *train* the concept generation
    # - test_df (pd.DataFrame): dataframe on which to *test* the concept generation
    # - out_text_col (str): name of the original output text column in the dataframe
    # - fixed_text_col (str): name of the fixed output text column in the dataframe
    # - in_text_col (str): name of the input text column in the dataframe to apply generation
    # - base_model (BaseModelLlama): the base model to use for training the intervention
    # - n (int): maximum number of df examples with which to perform generation
    # - n_epochs (int): number of epochs for intervention training
    # - n_trials (int): number of independent generations to produce
    def gen(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        out_text_col: str,
        fixed_text_col: str,
        in_text_col: str,
        base_model=None,
        n: int = 10,
        n_epochs: int = 30,
        n_trials: int = 3,
        debug: bool = False,
    ):
        import steering as s

        if base_model is None:
            base_model_path = "meta-llama/Meta-Llama-3-8B-Instruct"
            base_model = s.BaseModelLlama(
                model_name=base_model_path,
                torch_dtype=torch.bfloat16,
            )
        # Training: get paired pos and neg examples; train and cache model
        if self.interv is None:
            print("Training intervention...")
            train_start = time.time()
            # Create (positive, negative) pairs
            train_df_mod = self.format_reft_input(train_df, in_text_col, out_text_col)
            data_train = [
                (row[in_text_col], row[fixed_text_col])
                for _, row in train_df_mod.iterrows()
            ]
            if debug:
                print("Train examples:")
                print(data_train)
            print(f"Training with {len(data_train)} examples")

            interv = s.create_intervention(
                name=self.name,
                base_model=base_model,
                instruct_demo_pairs=data_train,
                num_train_epochs=n_epochs,
            )
            self.interv = interv
            train_time = time.time() - train_start
            print(f"Done training intervention! (time={train_time})")
        else:
            print("Intervention already trained!")

        # Eval: run on provided examples
        print("Evaluating intervention...")
        test_start = time.time()
        data_eval = test_df[in_text_col].tolist()
        df_gen = s.run_eval(
            eval_ex=data_eval,
            interv=self.interv,
            n_trials=n_trials,
        )
        test_time = time.time() - test_start
        print(f"Done testing intervention! (time={test_time})")
        return df_gen

    # Retrieves all policies that use this concept
    def get_policies(self):
        # TODO: create view to display associated policies
        return self.policies
