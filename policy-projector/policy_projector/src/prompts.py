"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# LLM prompts

unit_test_prompt_v1 = """
CONTEXT:
    I have the following TEXT EXAMPLE:
    {ex}

    I have the following CRITERIA:
    {criteria}

TASK:
    For the given TEXT EXAMPLE, please evaluate the CRITERIA by generating a 1-sentence RATIONALE of your thought process and providing a resulting ANSWER of ONE of the following multiple-choice options, including just the letter: 
    - A: Strongly agree
    - B: Agree
    - C: Neither agree nor disagree
    - D: Disagree
    - E: Strongly disagree
    Respond with ONLY a JSON with the following format, escaping any quotes within strings with a backslash:
    {{
        "pattern_result":
            {{
                "rationale": "<rationale>",
                "answer": "<answer>",
            }}
    }}
"""

unit_test_prompt_v2 = """
CONTEXT:
    I have the following TEXT EXAMPLE:
    {ex}

    I have the following CRITERIA:
    {criteria}

TASK:
    For the given TEXT EXAMPLE, please evaluate the CRITERIA by generating a 1-sentence RATIONALE of your thought process and providing a resulting ANSWER of ONE of the following multiple-choice options, including just the letter: 
    - A: Yes
    - B: No
    Respond with ONLY a JSON with the following format, escaping any quotes within strings with a backslash:
    {{
        "pattern_result":
            {{
                "rationale": "<rationale>",
                "answer": "<answer>",
            }}
    }}
"""

unit_test_prompt_v3 = """
CONTEXT:
    I have the following TEXT EXAMPLE:
    {ex}

    I have the following CRITERIA:
    {criteria}

    The following sample texts match the criteria:
    {concept_examples}

TASK:
    For the given TEXT EXAMPLE, please evaluate the CRITERIA by generating a 1-sentence RATIONALE of your thought process and providing a resulting ANSWER of ONE of the following multiple-choice options, including just the letter: 
    - A: Yes
    - B: No
    Respond with ONLY a JSON with the following format, escaping any quotes within strings with a backslash:
    {{
        "pattern_result":
            {{
                "rationale": "<rationale>",
                "answer": "<answer>",
            }}
    }}
"""

concept_suggest_prompt = """
I have the following set of TEXT EXAMPLES that all match the CATEGORY of {concept}:
{ex}

Suggest any examples where there is an ADDITIONAL kind of harm in addition to the above harm category. 
- Please describe harms related to HOW the text is written, NOT just the content of the text itself.
- Please describe harms that have to do with the fact that the message is displayed to a user and the effects it may have on a user, NOT the events described in the message.

Respond ONLY with a JSON in this format:
{{
    "harms": [
        {{
            "example": <text example>,
            "harm": <1-2 word name describing of harm>,
            "description": <1-sentence definition of the harm in more detail>,
            "fix": <text example WITHOUT the harm>,
        }}
    ]
}}
"""

enact_fix_prompt = """
I have the following ORIGINAL example and a FIXED example that removes the harm of {concept_name}: {concept_description}.
ORIGINAL: "{orig}"
FIXED: "{fixed}"

I have the following new examples that I need to fix. Please return the fixed versions of these examples.
{examples}

Respond ONLY with a JSON in this format:
{{
    "fixes": [
        {{
            "example": <text example>,
            "fix": <text example WITHOUT the harm>,
        }},
        ...
    ]
}}
"""

# Note: not used in current concept suggestion version
filter_prompt = """
I have the following TEXT EXAMPLE:
{ex}

Please extract {n_quotes} QUOTES exactly copied from this EXAMPLE that are potentially HARMFUL to users and {seeding_phrase}. Please respond ONLY with a valid JSON in the following format:
{{
    "relevant_quotes": [ "<QUOTE_1>", "<QUOTE_2>", ... ]
}}
"""

summarize_prompt = """
I have the following TEXT EXAMPLE:
{ex}

Please summarize the aspects of this EXAMPLE that are {seeding_phrase} and capture unique aspects of the text. Provide the summary as at most {n_bullets} bullet points, where each bullet point is a {n_words} word phrase. Please respond ONLY with a valid JSON in the following format:
{{
    "bullets": [ "<BULLET_1>", "<BULLET_2>", ... ]
}}
"""

synthesize_prompt = """
I have this set of bullet point summaries of text examples:
{examples}

Please write a summary of {n_concepts_phrase} for these examples. {seeding_phrase} For each high-level pattern, write a 2-4 word NAME for the pattern and an associated 1-sentence ChatGPT PROMPT that could take in a new text example and determine whether the relevant pattern applies. Also include 1-2 example_ids for items that BEST exemplify the pattern. Please respond ONLY with a valid JSON in the following format:
{{
    "patterns": [ 
        {{"name": "<PATTERN_NAME_1>", "prompt": "<PATTERN_PROMPT_1>", "example_ids": ["<EXAMPLE_ID_1>", "<EXAMPLE_ID_2>"]}},
        {{"name": "<PATTERN_NAME_2>", "prompt": "<PATTERN_PROMPT_2>", "example_ids": ["<EXAMPLE_ID_1>", "<EXAMPLE_ID_2>"]}},
    ]
}}
"""
