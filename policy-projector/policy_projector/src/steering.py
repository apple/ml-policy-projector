"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# Steering helpers

import os
import pandas as pd
import torch
import pyreft
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from pyreft import LoreftIntervention


def run_eval(
    eval_ex, interv, prompt_template=None, n_trials=3, max_new_tokens=128, debug=False
):
    if prompt_template is None:
        prompt_template = """
        Please summarize the following text into a one-sentence text message summary.
        
        ORIGINAL TEXT: 
        {orig}
        
        Please only return the single one-sentence summary.
        """

    rows = []
    for orig in eval_ex:
        # Run example over n_trials
        instruct = prompt_template.format(orig=orig)

        res_steer = interv.gen(
            instruction=instruct,
            max_new_tokens=max_new_tokens,
            num_return_sequences=n_trials,
        )

        res_base = interv.base_model.gen(
            instruction=instruct,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            num_return_sequences=n_trials,
        )
        # Unpack and save generations
        for i in range(n_trials):
            row = [instruct, orig, i, res_steer[i], res_base[i]]
            rows.append(row)

    df = pd.DataFrame(
        rows, columns=["Instruction", "Input", "Trial", "Steered gen", "Original gen"]
    )
    if debug:
        display(df[["Input", "Trial", "Steered gen", "Original gen"]])
    return df


def generate_examples(model, examples, n=10):
    template = """
    Please generate {n} more examples that are similar to these examples, but involve different topics:
    {examples}
    Please return the results as an array of strings.
"""
    out = model.gen(
        instruction=template.format(n=n, examples=examples),
        max_new_tokens=1000,
    )
    print(out)


def format_paired_prompt(model, examples, n=3):
    prompt_template = """
Please summarize the following text into a one-sentence text message summary.
    
ORIGINAL TEXT: 
{orig}

Please only return the single one-sentence summary.
"""

    final_template = """
Please summarize the following text into a one-sentence text message summary.
    
ORIGINAL TEXT: 
{orig}

DRAFT VERSION:
{neg}

Please only return the single one-sentence summary.
"""

    pairs = []
    for ex, goal in examples:
        for i in range(n):
            neg_prompt = prompt_template.format(orig=ex)
            neg = model.gen(
                instruction=neg_prompt,
                max_new_tokens=256,
                temperature=0.7,
            )
            cur_prompt = final_template.format(orig=ex, neg=neg)
            pair = (cur_prompt, goal)
            pairs.append(pair)

    return pairs


def format_paired_prompt2(examples):
    prompt_template = """
Please summarize the following text into a one-sentence text message summary.
    
ORIGINAL TEXT: 
{orig}

Please only return the single one-sentence summary.
"""

    pairs = []
    for ex, goal in examples:
        instruct = prompt_template.format(orig=ex)
        pair = (instruct, goal)
        pairs.append(pair)

    return pairs


def llama_post_process_func(x):
    x = x.replace("\r", "\n")
    x = x[x.find("assistant\n") + len("assistant\n") :] if "assistant\n" in x else x
    splits = x.strip().split("\n", 1)
    if len(splits) > 1 and ":" == splits[0].strip()[-1]:
        x = splits[1]
    return x.strip()


class BaseModelMistral:
    def __init__(self, model_name, torch_dtype):
        device = "cuda:0"  # change to "cpu" if there is not any CUDA GPU.
        self.model_name = model_name
        self.torch_dtype = torch_dtype
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_fast=False,
            model_max_length=2048,  # Hard code to avoid "no maximum length is provided"
        )
        self.tokenizer.pad_token = self.tokenizer.unk_token

    def gen(
        self,
        instruction,
        max_new_tokens,
        temperature,
        num_return_sequences=1,
        repetition_penalty=1.1,
    ):
        # No chat template
        inputs = self.tokenizer(instruction, return_tensors="pt").to(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        settings = {
            "pad_token_id": self.tokenizer.eos_token_id,  # silence warning
            "do_sample": True,
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
            "repetition_penalty": repetition_penalty,
            "num_return_sequences": num_return_sequences,
        }
        self.model = self.model.to("cuda" if torch.cuda.is_available() else "cpu")

        outputs = self.model.generate(**inputs, **settings)

        if num_return_sequences == 1:
            output = self.tokenizer.decode(
                outputs.squeeze()[inputs.input_ids.size(1) :], skip_special_tokens=True
            ).strip()
            # output = self.post_process_func(output)

        else:
            output = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            # output = [self.post_process_func(x.strip()) for x in output]

        return output


class BaseModelLlama:
    def __init__(self, model_name, torch_dtype, post_process_func=None):
        self.model_name = model_name
        self.torch_dtype = torch_dtype
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_fast=False,
            model_max_length=2048,
            padding_side="left",
        )

        self.tokenizer.add_special_tokens({"pad_token": "[PAD]"})
        self.model.resize_token_embeddings(len(self.tokenizer))
        self.model = self.model.cuda()

        self.post_process_func = post_process_func
        if self.post_process_func is None:
            self.post_process_func = llama_post_process_func

    def gen(
        self,
        instruction,
        max_new_tokens,
        temperature,
        num_return_sequences=1,
        repetition_penalty=1.1,
    ):
        # Chat template
        instruction_in_chat_template = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": instruction}], tokenize=False
        )
        inputs = self.tokenizer(instruction_in_chat_template, return_tensors="pt").to(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        settings = {
            "pad_token_id": self.tokenizer.eos_token_id,
            "do_sample": True,
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
            "repetition_penalty": repetition_penalty,
            "num_return_sequences": num_return_sequences,
        }
        self.model = self.model.to("cuda" if torch.cuda.is_available() else "cpu")

        outputs = self.model.generate(**inputs, **settings)

        if num_return_sequences == 1:
            output = self.tokenizer.decode(outputs, skip_special_tokens=True).strip()
            output = self.post_process_func(output)

        else:
            output = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            output = [self.post_process_func(x.strip()) for x in output]

        return output


class Interv:
    def __init__(
        self,
        base_model,
        params_dir,
        reft_config,
        add_system_prompt,
        post_process_func=None,
    ):
        self.base_model = base_model
        self.model = base_model.model
        self.tokenizer = base_model.tokenizer
        self.params_dir = params_dir
        self.reft_config = reft_config
        if add_system_prompt:
            self.system_prompt = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Directly fulfill the user's request without generating anything else.",
                }
            ]
        else:
            self.system_prompt = []

        self.post_process_func = post_process_func

    def gen(
        self,
        instruction: str,
        max_new_tokens: int,
        num_return_sequences: int = 1,
        **kwargs,
    ):
        model = self.model
        tokenizer = self.tokenizer
        params_dir = self.params_dir
        reft_config = self.reft_config

        # Initialize the PyReFT model
        layers = range(model.config.num_hidden_layers)
        reft_model = pyreft.get_reft_model(model, reft_config)

        # Load the saved PyReFT model
        interventions = {}
        for l in layers:
            component = f"model.layers[{l}].output"
            file_path = os.path.join(
                params_dir, f"intkey_comp.{component}.unit.pos.nunit.1#0.bin"
            )
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    adjusted_key = f"comp.{component}.unit.pos.nunit.1#0"
                    interventions[adjusted_key] = torch.load(f)

        # Apply the loaded weights to the model
        for component, state_dict in interventions.items():
            if component in reft_model.interventions:
                reft_model.interventions[component][0].load_state_dict(state_dict)
            else:
                print(
                    f"Key mismatch: {component} not found in reft_model.interventions"
                )

        # Set the device to CUDA
        reft_model.set_device("cuda")

        # Verify the model
        # reft_model.print_trainable_parameters()

        # PREV ----------------
        instruction_in_chat_template = tokenizer.apply_chat_template(
            self.system_prompt + [{"role": "user", "content": instruction}],
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(instruction_in_chat_template, return_tensors="pt").to(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # position info about the interventions
        share_weights = (
            True  # whether the prefix and suffix interventions sharing weights.
        )
        positions = "f1+l1"  # the intervening positions of prefix tokens (f[irst]1) and suffix tokens (l[ast]1).
        first_n, last_n = pyreft.parse_positions(positions)
        unit_locations = (
            torch.IntTensor(
                [
                    pyreft.get_intervention_locations(
                        last_position=inputs["input_ids"].shape[-1],
                        first_n=first_n,
                        last_n=last_n,
                        pad_mode="last",
                        num_interventions=len(self.reft_config.representations),
                        share_weights=share_weights,
                    )
                ]
            )
            .permute(1, 0, 2)
            .tolist()
        )

        # this should be as simple as repeating the input shape.
        if num_return_sequences > 1:
            for k in inputs:
                inputs[k] = inputs[k].repeat(num_return_sequences, 1)

        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]

        _, reft_response = reft_model.generate(
            inputs,
            unit_locations={"sources->base": (None, unit_locations)},
            intervene_on_prompt=True,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            eos_token_id=terminators,
            early_stopping=True,
            # intervention_kwargs={"weight": cur_strength}
        )

        output = None

        if num_return_sequences == 1:
            output = tokenizer.decode(
                reft_response[0], skip_special_tokens=True
            ).strip()
            output = self.post_process_func(output)

        else:
            output = tokenizer.batch_decode(reft_response, skip_special_tokens=True)
            output = [self.post_process_func(x.strip()) for x in output]

        return output

    def make_data_module(
        self, instruct_demo_pairs, share_weights=True, positions="f1+l1"
    ):
        bos_token = "system"  # Prefix before system response
        data_module = pyreft.make_multiple_position_supervised_data_module(
            self.tokenizer,
            self.model,
            [
                self.tokenizer.apply_chat_template(
                    self.system_prompt + [{"role": "user", "content": e[0]}],
                    add_generation_prompt=True,
                    tokenize=False,
                )
                for e in instruct_demo_pairs
            ],
            [
                self.tokenizer.apply_chat_template(
                    [{"role": "assistant", "content": e[1]}],
                    tokenize=False,
                )[len(bos_token) :]
                for e in instruct_demo_pairs  # Removes prefix
            ],
            positions=positions,
            num_interventions=len(self.reft_config.representations),
            share_weights=share_weights,
            nonstop=False,
        )

        return data_module

    def train(
        self,
        instruct_demo_pairs,
        num_train_epochs=20,
        learning_rate=4e-3,
        per_device_train_batch_size=10,
    ):
        padding_side = self.tokenizer.padding_side
        self.tokenizer.padding_side = "right"
        reft_model = pyreft.get_reft_model(self.model, self.reft_config)
        reft_model.set_device("cuda")

        share_weights = True
        positions = "f1+l1"
        data_module = self.make_data_module(
            instruct_demo_pairs, share_weights, positions
        )

        training_args = transformers.TrainingArguments(
            num_train_epochs=num_train_epochs,
            output_dir="./tmp",
            per_device_train_batch_size=per_device_train_batch_size,
            learning_rate=learning_rate,
            report_to=[],
            logging_steps=1,
        )
        trainer = pyreft.ReftTrainerForCausalLM(
            model=reft_model,
            tokenizer=self.tokenizer,
            args=training_args,
            **data_module,
        )
        _ = trainer.train()

        reft_model.set_device("cpu")

        reft_model.save(save_directory=self.params_dir)
        self.tokenizer.padding_side = padding_side


class IntervLlama:
    def __init__(
        self,
        base_model,
        params_dir,
        reft_config,
        add_system_prompt,
        post_process_func=None,
    ):
        self.base_model = base_model
        self.model = base_model.model
        self.tokenizer = base_model.tokenizer
        self.params_dir = params_dir
        self.reft_config = reft_config
        if add_system_prompt:
            self.system_prompt = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Please directly fulfill the user's request without providing any additional content.",
                }
            ]
        else:
            self.system_prompt = []

        self.post_process_func = post_process_func
        if self.post_process_func is None:
            self.post_process_func = llama_post_process_func

    def gen(
        self,
        instruction: str,
        max_new_tokens: int,
        num_return_sequences: int = 1,
        **kwargs,
    ):
        model = self.model
        tokenizer = self.tokenizer
        params_dir = self.params_dir
        reft_config = self.reft_config

        reft_model = pyreft.ReftModel.load(self.params_dir, model)
        reft_model.set_device("cuda")

        instruction_in_chat_template = tokenizer.apply_chat_template(
            self.system_prompt + [{"role": "user", "content": instruction}],
            tokenize=False,
        )
        inputs = tokenizer(instruction_in_chat_template, return_tensors="pt").to(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        share_weights = True
        positions = "f1+l1"
        first_n, last_n = pyreft.parse_positions(positions)
        unit_locations = (
            torch.IntTensor(
                [
                    pyreft.get_intervention_locations(
                        last_position=inputs["input_ids"].shape[-1],
                        first_n=first_n,
                        last_n=last_n,
                        pad_mode="last",
                        num_interventions=len(self.reft_config.representations),
                        share_weights=share_weights,
                    )
                ]
            )
            .permute(1, 0, 2)
            .tolist()
        )

        if num_return_sequences > 1:
            for k in inputs:
                inputs[k] = inputs[k].repeat(num_return_sequences, 1)

        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]

        _, reft_response = reft_model.generate(
            inputs,
            unit_locations={"sources->base": (None, unit_locations)},
            intervene_on_prompt=True,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            eos_token_id=terminators,
            early_stopping=True,
        )

        output = None

        if num_return_sequences == 1:
            output = tokenizer.decode(
                reft_response[0], skip_special_tokens=True
            ).strip()
            output = self.post_process_func(output)

        else:
            output = tokenizer.batch_decode(reft_response, skip_special_tokens=True)
            output = [self.post_process_func(x.strip()) for x in output]

        return output

    def make_data_module(
        self, instruct_demo_pairs, share_weights=True, positions="f1+l1"
    ):
        inputs = [
            self.tokenizer.apply_chat_template(
                self.system_prompt + [{"role": "user", "content": ex[0]}],
                tokenize=False,
            )
            for ex in instruct_demo_pairs
        ]

        outputs = [
            self.tokenizer.apply_chat_template(
                [{"role": "assistant", "content": ex[1]}],
                tokenize=False,
            )[len(self.tokenizer.bos_token) :]
            for ex in instruct_demo_pairs
        ]

        data_module = pyreft.make_multiple_position_supervised_data_module(
            self.tokenizer,
            self.model,
            inputs,
            outputs,
            positions=positions,
            num_interventions=len(self.reft_config.representations),
            share_weights=share_weights,
            nonstop=False,
        )

        return data_module

    def train(
        self,
        instruct_demo_pairs,
        num_train_epochs=20,
        learning_rate=4e-3,
        per_device_train_batch_size=10,
    ):
        # Reft requires setting tokenizer.padding_side to "right".
        padding_side = self.tokenizer.padding_side
        self.tokenizer.padding_side = "right"
        reft_model = pyreft.get_reft_model(self.model, self.reft_config)
        reft_model.set_device("cuda")  # FIXME: Hard code here.

        # position info about the interventions
        share_weights = (
            True  # whether the prefix and suffix interventions sharing weights.
        )
        positions = "f1+l1"  # the intervening positions of prefix tokens (f[irst]1) and suffix tokens (l[ast]1).
        data_module = self.make_data_module(
            instruct_demo_pairs, share_weights, positions
        )

        # Train.
        training_args = transformers.TrainingArguments(
            num_train_epochs=num_train_epochs,
            output_dir="./tmp",
            per_device_train_batch_size=per_device_train_batch_size,
            learning_rate=learning_rate,
            report_to=[],
            logging_steps=1,
        )
        trainer = pyreft.ReftTrainerForCausalLM(
            model=reft_model,
            tokenizer=self.tokenizer,
            args=training_args,
            **data_module,
        )
        _ = trainer.train()

        reft_model.set_device("cpu")

        reft_model.save(save_directory=self.params_dir)
        self.tokenizer.padding_side = padding_side


class IntervMistral:
    def __init__(self, base_model, params_dir, reft_config, add_system_prompt):
        self.base_model = base_model
        self.model = base_model.model
        self.tokenizer = base_model.tokenizer
        self.params_dir = params_dir
        self.reft_config = reft_config
        if add_system_prompt:
            self.system_prompt = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Directly fulfill the user's request without generating anything else.",
                }
            ]
        else:
            self.system_prompt = []

    def gen(
        self,
        instruction: str,
        max_new_tokens: int,
        num_return_sequences: int = 1,
        **kwargs,
    ):
        model = self.model
        tokenizer = self.tokenizer
        params_dir = self.params_dir
        reft_config = self.reft_config

        # Initialize the PyReFT model
        reft_model = pyreft.ReftModel.load(self.params_dir, model)
        reft_model.set_device("cuda")  # FIXME: Hard code here.

        # No chat template
        inputs = tokenizer(instruction, return_tensors="pt").to(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # position info about the interventions
        share_weights = (
            True  # whether the prefix and suffix interventions sharing weights.
        )
        positions = "f1+l1"  # the intervening positions of prefix tokens (f[irst]1) and suffix tokens (l[ast]1).
        first_n, last_n = pyreft.parse_positions(positions)
        unit_locations = (
            torch.IntTensor(
                [
                    pyreft.get_intervention_locations(
                        last_position=inputs["input_ids"].shape[-1],
                        first_n=first_n,
                        last_n=last_n,
                        pad_mode="last",
                        num_interventions=len(self.reft_config.representations),
                        share_weights=share_weights,
                    )
                ]
            )
            .permute(1, 0, 2)
            .tolist()
        )

        # this should be as simple as repeating the input shape.
        if num_return_sequences > 1:
            for k in inputs:
                inputs[k] = inputs[k].repeat(num_return_sequences, 1)

        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]

        _, reft_response = reft_model.generate(
            inputs,
            unit_locations={"sources->base": (None, unit_locations)},
            intervene_on_prompt=True,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            eos_token_id=terminators,
            early_stopping=True,
            # intervention_kwargs={"weight": cur_strength}
        )

        output = None

        if num_return_sequences == 1:
            output = tokenizer.decode(
                reft_response[0], skip_special_tokens=True
            ).strip()

        else:
            output = tokenizer.batch_decode(reft_response, skip_special_tokens=True)

        return output

    def make_data_module(
        self, instruct_demo_pairs, share_weights=True, positions="f1+l1"
    ):
        inputs = [e[0] for e in instruct_demo_pairs]
        outputs = [e[1] for e in instruct_demo_pairs]

        data_module = pyreft.make_multiple_position_supervised_data_module(
            self.tokenizer,
            self.model,
            inputs,
            outputs,
            positions=positions,
            num_interventions=len(self.reft_config.representations),
            share_weights=share_weights,
            nonstop=False,
        )

        return data_module

    def train(
        self,
        instruct_demo_pairs,
        num_train_epochs=20,
        learning_rate=4e-3,
        per_device_train_batch_size=10,
    ):
        # Reft requires setting tokenizer.padding_side to "right".
        padding_side = self.tokenizer.padding_side
        self.tokenizer.padding_side = "right"
        reft_model = pyreft.get_reft_model(self.model, self.reft_config)
        reft_model.set_device("cuda")  # FIXME: Hard code here.

        # position info about the interventions
        share_weights = (
            True  # whether the prefix and suffix interventions sharing weights.
        )
        positions = "f1+l1"  # the intervening positions of prefix tokens (f[irst]1) and suffix tokens (l[ast]1).
        data_module = self.make_data_module(
            instruct_demo_pairs, share_weights, positions
        )

        # Train.
        training_args = transformers.TrainingArguments(
            num_train_epochs=num_train_epochs,
            output_dir="./tmp",
            per_device_train_batch_size=per_device_train_batch_size,
            learning_rate=learning_rate,
            report_to=[],
            logging_steps=1,
        )
        trainer = pyreft.ReftTrainerForCausalLM(
            model=reft_model,
            tokenizer=self.tokenizer,
            args=training_args,
            **data_module,
        )
        _ = trainer.train()

        reft_model.set_device("cpu")

        reft_model.save(save_directory=self.params_dir)
        self.tokenizer.padding_side = padding_side


def create_intervention(
    name: str,
    base_model: str,
    instruct_demo_pairs,
    num_train_epochs: int = 40,
    add_system_prompt: bool = False,
    **kwargs,
):
    params_dir = f'./{name.replace(" ", "_")}_reft_model'

    if "Llama" in base_model.model_name:
        reft_config = pyreft.ReftConfig(
            representations=[
                {
                    "layer": l,
                    "component": "block_output",
                    "low_rank_dimension": 2,
                    "intervention": LoreftIntervention(
                        embed_dim=base_model.model.config.hidden_size,
                        low_rank_dimension=2,
                    ),
                }
                for l in [8, 16, 24]
            ]
        )

        intervention = IntervLlama(
            base_model=base_model,
            params_dir=params_dir,
            reft_config=reft_config,
            add_system_prompt=add_system_prompt,
        )
    elif "Mistral" in base_model.model_name:
        reft_config = pyreft.ReftConfig(
            representations=[
                {
                    "layer": l,
                    "component": "block_output",
                    "low_rank_dimension": 2,
                    "intervention": LoreftIntervention(
                        embed_dim=base_model.model.config.hidden_size,
                        low_rank_dimension=2,
                    ),
                }
                for l in [8, 16, 24]
            ]
        )

        intervention = IntervMistral(
            base_model=base_model,
            params_dir=params_dir,
            reft_config=reft_config,
            add_system_prompt=add_system_prompt,
        )

    training_pairs = instruct_demo_pairs

    intervention.train(
        instruct_demo_pairs=training_pairs, num_train_epochs=num_train_epochs
    )
    return intervention


def print_data(data_in):
    data = [d[0] for d in data_in]
    for d in data:
        print(f"\n\n{d}")
