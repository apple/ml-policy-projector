"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# Case
import pandas as pd
import copy
from typing import Dict
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets

import prompts as p
from dataset import Dataset

# # Local imports
# if __package__ is None or __package__ == '':
#     # uses current directory visibility
#     from __init__ import TableWidget
# else:
#     # uses current package visibility
#     from . import TableWidget


class Case:

    # Case setup
    def __init__(self, spec, nav, cur_id=None):
        spec = copy.deepcopy(spec)
        self.name = spec["name"]
        self.description = spec["description"]
        self.examples = Dataset.from_json(spec["examples"])
        self.fixes = Dataset.from_json(spec["fixes"])
        self.existing_concept = spec["existing_concept"]

        self.id = cur_id

        # Create preliminary version of concept and policy, which will be updated
        self.concept = self.__create_concept(nav)
        self.policy = self.__create_policy(nav)
        self.base_model = nav.base_model

    # Creates a new concept with the current case spec
    def __create_concept(self, nav):
        spec = {
            "name": self.name,
            "description": self.description,
            "examples": self.examples.to_json(),
            "fixes": self.fixes.to_json(),
        }
        c = nav.add_concept(spec)
        return c

    # Creates a new policy with the current concept
    def __create_policy(self, nav):
        if_conditions = [
            self.existing_concept,
            self.concept.name,
        ]  # TODO: handle other options for if-conditions
        then_actions = [self.concept.name]  # TODO: handle other possible then-actions
        spec = {
            "name": self.name,
            "description": self.description,
            "if": if_conditions,
            "then": then_actions,
            "examples": self.examples.to_json(),
            "fixes": self.fixes.to_json(),
        }
        p = nav.add_policy(spec)
        return p

    def get_input_text(self):
        return self.examples.get(self.examples.in_text_col).tolist()[0]

    def get_orig_gen(self):
        return self.examples.get(self.examples.out_text_col).tolist()[0]

    def get_fixed_gen(self):
        return self.fixes.get(self.fixes.out_text_col).tolist()[0]

    # # Displays the current candidate description of the case in an editable text box
    # # On user edit and submission, updates the concept description (creating a concept if it doesn't yet exist)
    # def describe(self):
    #     # Display case
    #     print(f"Original input:\n\t{self.get_input_text()}")
    #     print(f"\nOriginal generation:\n\t{self.get_orig_gen()}")

    #     print("\nWhat's going wrong in this case? Edit the description below to describe the category of harm in your own words.")
    #     w_desc = widgets.Textarea(
    #         value=self.description,
    #         description='Description:',
    #         disabled=False,
    #         layout=widgets.Layout(width='auto', height='auto'),
    #         style= {'description_width': 'initial'}
    #     )

    #     # Executes the update to concept description
    #     def describe_update(desc):
    #         self.description = desc
    #         # Update concept
    #         self.concept.description = self.description
    #         print("Updated description!")

    #     my_interact_manual = interact_manual.options(manual_name="Submit")
    #     my_interact_manual(describe_update, desc=w_desc)

    # # Displays the current candidate fix for the case in an editable text box
    # # On user edit and submission, updates the fix (creating a concept if it doesn't yet exist)
    # def fix(self):
    #     # Display case
    #     print(f"Original input:\n\t{self.get_input_text()}")
    #     print(f"\nOriginal generation:\n\t{self.get_orig_gen()}")

    #     print("\nWhat should be the fixed version of this case? Edit the text below to demonstrate the ideal summary that the system would generate instead of the original generation.")
    #     w_fixed = widgets.Textarea(
    #         value=self.get_fixed_gen(),
    #         description='Fixed generation:',
    #         disabled=False,
    #         layout=widgets.Layout(width='auto', height='auto'),
    #         style= {'description_width': 'initial'}
    #     )

    #     # Executes the update to the concept's fixed example
    #     def fix_update(fixed_example):
    #         self.examples[0]["neg_text"] = fixed_example
    #         # Update concept
    #         self.concept.examples = self.examples
    #         print("Updated fix!")

    #     my_interact_manual = interact_manual.options(manual_name="Submit")
    #     my_interact_manual(fix_update, fixed_example=w_fixed)

    # Retrieves similar cases based on the underlying concept description
    # - df (pd.DataFrame): dataframe to classify to retrieve similar cases
    # - out_text_col (str): name of the text column in the dataframe for which to classify the concept
    # - in_text_col (str): name of df column with input text
    # - id_col (str): name of df column with unique IDs
    # - n (int): maximum number of df examples to classify
    async def find_similar(
        self,
        df: pd.DataFrame,
        out_text_col: str,
        in_text_col: str,
        id_col: str,
        concept_col: str = None,
        n: int = 20,
        debug=False,
    ):
        if (self.existing_concept is not None) and (concept_col is not None):
            df = df[df[concept_col] == self.existing_concept]
        w = await self.policy.match(
            df,
            col=out_text_col,
            id_col=id_col,
            in_text_col=in_text_col,
            n=n,
            debug=debug,
        )
        return w

    # Applies the same fix as indicated in the case on the provided (similar) cases
    # - df (pd.DataFrame): dataframe with examples to fix
    # - out_text_col (str): name of df column with output text to fix
    # - in_text_col (str): name of df column with input text
    # - id_col (str): name of df column with unique IDs
    # - model_name (str): model to use to suggest the fixes
    def fix_similar(
        self,
        df: pd.DataFrame,
        out_text_col: str,
        in_text_col: str,
        id_col: str,
        model_name: str,
        debug=False,
    ):
        if debug:
            fixes = [
                {"example": ex, "fix": "This is a sample fix."}
                for ex in df[out_text_col].tolist()
            ]
        else:
            # Run prompt to enact suggested fixes for the provided examples
            prompt_template = p.enact_fix_prompt
            ex = df[
                out_text_col
            ].tolist()  # TODO: adapt to handle input and/or output text
            orig = self.get_input_text()
            fixed = self.get_fixed_gen()
            prompt = prompt_template.format(
                concept_name=self.concept.name,
                concept_description=self.concept.description,
                orig=orig,
                fixed=fixed,
                examples=ex,
            )
            res = complete.to_dict(prompt, model_name=model_name)
            fixes = res["fixes"]

        # Parse results
        for fix, cur_id in zip(fixes, df[id_col].tolist()):
            fix[id_col] = cur_id
        fix_df = pd.DataFrame(fixes)[[id_col, "fix"]]
        fix_df = df.merge(fix_df, on=id_col)

        # Display results and add to concept
        fix_examples = Dataset(
            df=fix_df,
            id_col=id_col,
            in_text_col=in_text_col,
            out_text_col=out_text_col,
            score_col="score",
            source_col="source",
            cols=[in_text_col, out_text_col, "fix", id_col, "score", "source"],
        )
        # w = TableWidget(
        #     obj=self.concept,
        #     obj_type="Concept",
        #     dataset=fix_examples,
        #     cols_to_show=[in_text_col, out_text_col, "fix", id_col, "score", "source"],
        #     text_cols=[in_text_col, out_text_col, "fix"],
        #     edit_type="Fix",
        #     editable_cols=["fix"],
        # )
        # return w

    # Scales up the demonstrated fixes to a steering intervention
    # - df (pd.DataFrame): dataframe on which to run the policy generation
    # - in_text_col (str): name of the input text column in the dataframe to apply generation
    # - n (int): maximum number of df examples with which to perform generation
    # - n_epochs (int): number of epochs for intervention training
    # - n_trials (int): number of independent generations to produce
    def train_fix(
        self,
        df: pd.DataFrame,
        in_text_col: str,
        n: int = 10,
        n_epochs: int = 30,
        n_trials: int = 3,
    ):
        df_gen = self.policy.act(
            df, in_text_col, self.base_model, n, n_epochs, n_trials
        )
        return df_gen
