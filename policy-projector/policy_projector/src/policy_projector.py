"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# Policy Projector
import pandas as pd
from ipywidgets import interact
import ipywidgets as widgets
import json
from typing import Optional
import os

import util
import prompts as p
from policy import Policy
from concept import Concept
from case import Case

# LLooM import (using testPyPI)
# pip install --extra-index-url https://test.pypi.org/simple/ text_lloom==0.7.6.2
import text_lloom.workbench as wb
from text_lloom.llm import OpenAIModel, OpenAIEmbedModel


class PolicyProjector:

    # Policy Projector setup
    # - df (pd.DataFrame): dataframe with which to develop policy
    # - id_col (str): name of df column with unique IDs
    # - in_text_col (str): name of df column with *input* text to analyze
    # - out_text_col (str): name of df column with *output* text to analyze
    # - concept_col (str): (optional) name of df column with existing concept names
    # - score_col (str): (optional) name of df column with existing concept scores
    # - auto_populate (bool): whether to auto-populate the Projector with concepts from concept_col. Default: True
    # - auto_populate_limit (int): maximum number of concepts to auto-populate
    # - base_model_path (str): path to the base model to use for generation
    def __init__(
        self,
        df: pd.DataFrame,
        id_col: str,
        in_text_col: str,
        out_text_col: str,
        concept_col: Optional[str] = None,
        score_col: Optional[str] = None,
        auto_populate: bool = True,
        auto_populate_limit: int = 20,
        base_model_path=None,
    ):
        # Dataframe information
        self.df = df
        self.id_col = id_col
        self.in_text_col = in_text_col
        self.out_text_col = out_text_col
        self.concept_col = concept_col
        if score_col is not None:
            self.score_col = score_col
        else:
            self.score_col = "score"
        self.source_col = "source"

        # Concepts and policies
        self.concepts = {}
        if auto_populate:
            if concept_col is None:
                raise Exception(
                    "Please provide a `concept_col` in order to auto-populate concepts."
                )
            self.__auto_populate_concepts_from_col(
                self.df, self.concept_col, source="manual", limit=auto_populate_limit
            )

        self.policies = {}
        self.cases = {}

        if base_model_path is not None:
            import steering as s

            self.base_model = s.BaseModelLlama(
                model_name=base_model_path,
            )
        else:
            self.base_model = None

        print(
            f"Created PolicyProjector (concepts: {len(self.concepts)}, policies: {len(self.policies)})"
        )

    # Auto-populates concepts based on concept column
    # - df (pd.DataFrame): dataframe with which to develop policy
    # - concept_col (str): name of df column with existing concept names
    # - source (str): name of the source of the concept labels
    # - limit (int): maximum number of concepts to auto-create
    def __auto_populate_concepts_from_col(
        self, df: pd.DataFrame, concept_col: str, source: str, limit: int = None
    ):
        concept_options = df[concept_col].unique().tolist()
        # Create Concept for each unique concept option in df
        for i, concept_option in enumerate(concept_options):
            if (limit is not None) and i == limit:
                return

            concept_df = df[df[concept_col] == concept_option]
            example_ids = concept_df[self.id_col].tolist()
            cur_id = len(self.concepts) + 1
            concept_spec = {
                "name": concept_option,
                "description": f"These examples were manually labeled with the label {concept_option}",  # TODO: auto-generate description
                "examples": example_ids,
                "fixes": None,
                "id": cur_id,
            }
            c = self.add_concept(concept_spec, label_col=concept_col)

    # Performs the filtering to a specified concept column
    # - selected_concept (str): name of concept to filter to
    def __filter_by_concept_helper(self, selected_concept: str):
        # Create df based on this concept's examples
        c = self.get_concept(name=selected_concept)
        return c.view(self.df, self.id_col, self.in_text_col, self.out_text_col)

    # Displays widget to select a concept with which to filter the dataframe
    def __filter_by_concepts(self):
        def get_formatted_name(c):
            return f"{c.name}, (n={len(c.examples)})"

        concept_options = [
            (get_formatted_name(c), c.name) for c in self.concepts.values()
        ]

        w = widgets.Dropdown(
            options=concept_options,
            value=concept_options[0][1],
            description="Concepts:",
            disabled=False,
            layout=widgets.Layout(width="auto"),
            style={"description_width": "initial"},
        )

        interact(self.__filter_by_concept_helper, selected_concept=w)

    # Displays global web viewer to see all concepts
    def view(self):
        # TODO: Implement full version
        self.__filter_by_concepts()

    # Displays a widget for the specified concept (using either the concept or its name)
    # - c (Concept): the concept object to view
    # - name (str): the name of the concept to view
    def view_concept(self, c=None, name=None):
        if name is not None and c is None:
            c = self.get_concept(name=name)
        return c.view(self.df, self.id_col, self.in_text_col, self.out_text_col)

    # Displays a widget for the specified policy (using either the policy or its name)
    # - p (Policy): the policy object to view
    # - id (str): the id of the policy to view
    def view_policy(self, p=None, p_id=None):
        if p_id is not None and p is None:
            p = self.get_policy(p_id=p_id)
        return p.view(self.df, self.id_col, self.in_text_col, self.out_text_col)

    # Suggests potentially problematic cases for the user to review
    # - min_examples (int): minimum number of examples required to include a concept
    async def suggest_cases(self, min_examples: int = 20, debug=False):
        eligible_concepts = [
            c for c in self.concepts.values() if (c.examples.count() >= min_examples)
        ]
        suggestions = []
        specs = []
        if debug:
            import cached.suggest_cases as cache

            specs = cache.specs
            suggestions = cache.suggestions
        else:
            for concept in eligible_concepts:
                suggested_cases, suggested_specs = await self.suggest_concepts(
                    concept.name, interactive=False, debug=False
                )
                for c in suggested_cases:
                    c["existing_concept"] = concept.name
                suggestions.extend(suggested_cases)
                specs.extend(suggested_specs)

        # Display suggested cases
        print(f"Potential cases (n={len(suggestions)}):")
        suggestion_df = pd.DataFrame(suggestions)
        cols_to_show = ["harm", "example", "existing_concept"]
        display(suggestion_df[cols_to_show])

        suggestion_opts = [(f'{i}: {s["name"]}', s) for i, s in enumerate(specs)]
        w = widgets.Dropdown(
            options=suggestion_opts,
            value=suggestion_opts[0][1],
            description="Select a case:",
            disabled=False,
            layout=widgets.Layout(width="auto"),
            style={"description_width": "initial"},
        )
        display(w)
        return w

    def get_summ_prompt(self, existing_concepts_str):
        summ_prompt = (
            """
I have the following TEXT EXAMPLE:
{ex}

I have this set of EXISTING CONCEPTS:
"""
            + existing_concepts_str
            + """

Please summarize the aspects of this EXAMPLE that are {seeding_phrase} and capture unique aspects of the text that are NOT captured by the EXISTING CONCEPTS. Provide the summary as at most {n_bullets} bullet points, where each bullet point is a {n_words} word phrase. Please respond ONLY with a valid JSON in the following format:
{{
    "bullets": [ "<BULLET_1>", "<BULLET_2>", ... ]
}}
"""
        )
        return summ_prompt

    def get_synth_prompt(self, existing_concepts_str):
        synth_prompt = (
            """
I have this set of bullet point summaries of text examples:
{examples}

I have this set of EXISTING CONCEPTS:
"""
            + existing_concepts_str
            + """

Please write a summary of {n_concepts_phrase} for these examples. {seeding_phrase} These patterns should NOT overlap with the EXISTING CONCEPTS. For each high-level pattern, write a 2-4 word NAME for the pattern and an associated 1-sentence ChatGPT PROMPT that could take in a new text example and determine whether the relevant pattern applies. Also include 1-2 example_ids for items that BEST exemplify the pattern. Please respond ONLY with a valid JSON in the following format:
{{
    "patterns": [ 
        {{"name": "<PATTERN_NAME_1>", "prompt": "<PATTERN_PROMPT_1>", "example_ids": ["<EXAMPLE_ID_1>", "<EXAMPLE_ID_2>"]}},
        {{"name": "<PATTERN_NAME_2>", "prompt": "<PATTERN_PROMPT_2>", "example_ids": ["<EXAMPLE_ID_1>", "<EXAMPLE_ID_2>"]}},
    ]
}}
"""
        )
        return synth_prompt

    # Displays suggestion in concept spec form
    def get_concept_spec(
        self,
        c,
        ex_key="examples",
        fix_key="fixes",
        name_key="harm",
        desc_key="description",
    ):
        spec = {
            "name": c[name_key],
            "description": c[desc_key],
            "examples": list(c[ex_key]),  # example IDs
            "fixes": c[fix_key],
            "existing_concept": "",  # TODO: modify field to track provenance
        }
        return spec

    def display_concept_spec(self, c):
        spec = self.get_concept_spec(c)
        # Print spec nicely
        spec_str = json.dumps(spec, indent=2)
        print(spec_str)

    # Displays suggestion in policy spec form
    def get_policy_spec(
        self,
        c,
        ex_key="examples",
        fix_key="fixes",
        name_key="harm",
        desc_key="description",
    ):
        new_concept_name = c[name_key]
        spec = {
            "name": new_concept_name,
            "description": c[desc_key],
            "if": [new_concept_name],
            "examples": list(c[ex_key]),  # example IDs
        }
        return spec

    def display_policy_spec(self, c):
        spec = self.get_policy_spec(c)
        # Print spec nicely
        spec_str = json.dumps(spec, indent=2)
        print(spec_str)

    # Solicits suggestions on new concepts from full dataset or filtered subset.
    # - filter_ids (List[str]): example IDs to filter dataset. If none is provided, generates suggestions across full dataset.
    # - existing_concepts (List[str]): existing concepts in the taxonomy (which shouldn't be repeated among suggestions)
    # - spec_to_show (str): which type of spec to show (options: "policy" or "concept")
    # - limit (str): maximum number of concept examples to provide as input to concept suggestion prompt
    # - interactive (bool): whether to show interactive view (default: True); otherwise, just returns the suggestions
    async def suggest_concepts(
        self,
        filter_ids=[],
        existing_concepts=[],
        spec_to_show="concept",
        limit: int = None,
        interactive: bool = True,
        debug=True,
    ):
        # Prompt LLM to suggest boundary cases from a set of examples
        df = self.df.copy()

        # Filter df to provided IDs and truncate to specified limit
        if len(filter_ids) > 0:
            df = df[df[self.id_col].isin(filter_ids)]

        if limit is not None:
            limit = min(len(df), limit)
            df = df.sample(n=limit)

        print(f"filter_ids: n={len(filter_ids)}")
        print(f"filtered df: n={len(df)}")

        name_key = "harm"
        desc_key = "description"
        ex_key = "examples"
        fix_key = "fixes"

        if debug:
            import cached.suggest_concepts as cache

            res = cache.res
        else:
            # Run LLooM
            openai_key = os.environ["OPENAI_API_KEY"]
            l = wb.lloom(
                df=df,
                id_col="id",
                text_col="model_output",
                distill_model=OpenAIModel(
                    name="gpt-4o-mini",
                    api_key=openai_key,
                    context_window=128_000,
                    cost=(0.15 / 1_000_000, 0.6 / 1_000_000),
                    rate_limit=(300, 10),
                ),
                cluster_model=OpenAIEmbedModel(
                    name="text-embedding-3-large", api_key=openai_key
                ),
                synth_model=OpenAIModel(
                    name="gpt-4o",
                    api_key=openai_key,
                    context_window=128_000,
                    cost=(5 / 1_000_000, 15 / 1_000_000),
                    rate_limit=(20, 10),
                ),
                score_model=OpenAIModel(
                    name="gpt-4o-mini",
                    api_key=openai_key,
                    context_window=128_000,
                    cost=(0.15 / 1_000_000, 0.6 / 1_000_000),
                    rate_limit=(300, 10),
                ),
            )

            # Prep prompts
            if len(existing_concepts) > 0:
                existing_concepts_str = "- " + "\n- ".join(existing_concepts)
                summ_prompt = self.get_summ_prompt(existing_concepts_str)
                synth_prompt = self.get_synth_prompt(existing_concepts_str)
            else:
                summ_prompt = p.summarize_prompt
                synth_prompt = p.synthesize_prompt

            await l.gen(
                seed="harmful concepts",
                custom_prompts={
                    "distill_filter": None,  # Skip filtering
                    "distill_summarize": summ_prompt,
                    "synthesize": synth_prompt,
                },
                debug=False,
            )

            # Parse results
            res = []
            for _, c in l.concepts.items():
                cur_res = {
                    name_key: c.name,
                    desc_key: c.prompt,
                    ex_key: c.example_ids,
                    fix_key: [],
                }
                res.append(cur_res)

        # Displays widget to view the spec associated with a suggestion
        if interactive:
            spec_options = [(r["harm"], r) for r in res]
            if spec_to_show == "concept":
                # Concept version
                print("Show concept spec:")
                w = widgets.Dropdown(
                    options=spec_options,
                    value=spec_options[0][1],
                    description="Concept:",
                    disabled=False,
                )
                interact(self.display_concept_spec, c=w)
            elif spec_to_show == "policy":
                # Policy version
                print("Show policy spec:")
                w = widgets.Dropdown(
                    options=spec_options,
                    value=spec_options[0][1],
                    description="Policy:",
                    disabled=False,
                )
                interact(self.display_policy_spec, c=w)
        else:
            suggestions = res
            specs = [self.get_concept_spec(c) for c in suggestions]
            return suggestions, specs

    # Adds case with the provided spec
    def add_case(self, spec):
        l = Case(spec, self)
        l_id = len(self.cases)
        self.cases[l_id] = l
        l.id = l_id
        return l

    # Adds concept with the provided spec
    def add_concept(self, spec, labeled=False, label_col=None):
        c = Concept(spec, labeled=labeled, label_col=label_col)
        c_id = c.id
        if c_id in self.concepts:
            raise Exception(
                f"Concept with id `{c_id}` already exists. Please provide a unique concept ID."
            )

        self.concepts[c_id] = c
        return c

    # Retrieves a concept by its name or ID. If not found, returns None.
    def get_concept(self, name=None, c_id=None):
        if c_id is not None:
            # Fetch by ID
            if c_id in self.concepts:
                return self.concepts[c_id]
        elif name is not None:
            # Fetch by name
            for c in self.concepts.values():
                if c.name == name:
                    return c
        return None

    # Adds policy with the provided spec
    def add_policy(self, spec):
        if_concepts = [self.get_concept(n) for n in spec["if"]]
        if_concept_specs = [
            c.to_spec(include_examples=True, return_dict=True) for c in if_concepts
        ]
        spec["if"] = if_concept_specs
        pol = Policy(spec)
        p_id = pol.id
        if p_id in self.policies:
            raise Exception(
                f"Policy with id `{p_id}` already exists. Please provide a unique policy ID."
            )

        self.policies[p_id] = pol
        return pol

    # Retrieves a policy by its ID. If not found, returns None.
    def get_policy(self, p_id):
        if p_id in self.policies:
            return self.policies[p_id]
        return None
