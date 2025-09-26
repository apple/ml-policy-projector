"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# LLM helper functions
import asyncio
import yaml
import os


def setupGPT():
    # GPT settings
    MODEL = Model(
        name="gpt-4o-mini",
        setup_fn=llm.setup_gpt,
        fn=llm.call_gpt,
        rate_limit=(300, 10),  # (n_requests, wait_time_secs)
    )

    # # Run one-time GPT setup
    MODEL.client = MODEL.setup_fn()


class Model:
    # Specification to run prompts on a specific large language model
    # - name: str, name of the model (ex: "gpt-3.5-turbo")
    # - setup_fn: function, function to set up the LLM client
    # - fn: function, function to call the model (i.e., to run LLM prompt)
    # - rate_limit: tuple, (n_requests, wait_time_secs)
    def __init__(self, name, setup_fn, fn, rate_limit, **args):
        self.name = name
        self.setup_fn = setup_fn
        self.fn = fn
        self.rate_limit = rate_limit
        self.args = args


# Helper for parsing a JSON output
def json_load(s, top_level_key=None):
    def get_top_level_key(d):
        if (top_level_key is not None) and top_level_key in d:
            d = d[top_level_key]
            return d
        return d

    # Attempts to safely load a JSON from a string response from the LLM
    if s is None:
        return None
    elif isinstance(s, dict):
        return get_top_level_key(s)
    json_start = s.find("{")
    json_end = s.rfind("}")
    s_trimmed = s[json_start : (json_end + 1)]

    try:
        cur_dict = yaml.safe_load(s_trimmed)
        return get_top_level_key(cur_dict)
    except:
        print(f"ERROR json_load on: {s}")
        return None


# Wrapper for calling the base LLM API
async def base_api_wrapper(cur_prompt, model):
    res = await model.fn(model, cur_prompt)
    return res


# GPT-specific helpers
# Set up GPT
def setup_gpt():
    from openai import AsyncOpenAI

    openai_key = os.environ["OPENAI_API_KEY"]
    llm_client = AsyncOpenAI(
        api_key=openai_key,
    )
    return llm_client


# Wrapper around call to GPT
async def call_gpt(model, prompt):
    system_prompt = "You are a helpful assistant."
    res_orig = await model.client.chat.completions.create(
        model=model.name,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    res = res_orig.choices[0].message.content if res_orig else None
    return res


# Internal function making calls to LLM; runs a single LLM query
async def multi_query_gpt(
    model, prompt_template, arg_dict, batch_num=None, wait_time=None, debug=False
):
    if wait_time is not None:
        if debug:
            print(f"Batch {batch_num}, wait time {wait_time}")
        await asyncio.sleep(wait_time)  # wait asynchronously

    try:
        prompt = prompt_template.format(**arg_dict)
        res = await base_api_wrapper(prompt, model)
    except Exception as e:
        print("Error", e)
        return None

    return res


# Run multiple LLM queries
async def multi_query_gpt_wrapper(
    prompt_template, arg_dicts, model, batch_num=None, batched=True, debug=False
):
    if debug:
        print("model_name", model.name)

    rate_limit = model.rate_limit
    if not batched:
        # Non-batched version
        tasks = [multi_query_gpt(model, prompt_template, args) for args in arg_dicts]
    else:
        # Batched version
        n_requests, wait_time_secs = rate_limit
        tasks = []
        arg_dict_batches = [
            arg_dicts[i : i + n_requests] for i in range(0, len(arg_dicts), n_requests)
        ]
        for inner_batch_num, cur_arg_dicts in enumerate(arg_dict_batches):
            if batch_num is None:
                wait_time = wait_time_secs * inner_batch_num
            else:
                wait_time = wait_time_secs * batch_num
            if debug:
                wait_time = 0  # Debug mode
            cur_tasks = [
                multi_query_gpt(
                    model,
                    prompt_template,
                    arg_dict=args,
                    batch_num=batch_num,
                    wait_time=wait_time,
                )
                for args in cur_arg_dicts
            ]
            tasks.extend(cur_tasks)

    res_text = await asyncio.gather(*tasks)
    tokens = None

    return res_text, tokens
