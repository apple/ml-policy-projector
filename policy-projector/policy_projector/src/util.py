"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# Utilities
import pandas as pd
from dataset import Dataset


# Dataframe helpers
# From the dataframe, retrieves an example's ID given the text
# Returns None if not found
# - df (pd.DataFrame): dataframe containing examples
# - ex (str): text of the example to retrieve
# - text_col (str): name of df column with text
# - id_col (str): name of df column with unique IDs
def get_ex_id(df: pd.DataFrame, ex: str, text_col: str, id_col: str):
    ex_row = df[df[text_col] == ex]
    if len(ex_row) == 0:
        return None
    ex_id = ex_row[id_col].tolist()[0]
    return ex_id


# From the dataframe, retrieves another column associated with an example given its ID
# Returns None if not found
# - df (pd.DataFrame): dataframe containing examples
# - ex_id (str): ID of the example to retrieve
# - id_col (str): name of df column with unique IDs
# - col (str): name of column value to retrieve
def get_ex_col(df: pd.DataFrame, ex_id: str, id_col: str, col: str):
    ex_row = df[df[id_col] == ex_id]
    if len(ex_row) == 0:
        return None
    ex_col = ex_row[col].tolist()[0]
    return ex_col


# Formats the dataframe into a list of rows including a row of column names
# Used for ActiveTable element
# - df (pd.DataFrame): dataframe to reformat
# - cols_to_show (list[str]): list of column names in df to include
def df_to_rows(df: pd.DataFrame, cols_to_show):
    df_rows = [cols_to_show]  # Add header row
    df_rows.extend(df.values.tolist())  # Add data rows
    return df_rows


# Formats the rows (header row and data rows) into a dataframe
# Used to translate from ActiveTable format
# - rows (list[list[Any]]): list of dataframe rows to include in df, where the first row is a list of column names
def rows_to_df(rows):
    cols_to_show = rows[0]  # Get header row
    df = pd.DataFrame(rows[1:], columns=cols_to_show)  # Get data rows
    return df


# Given example IDs and df, return a corresponding Dataset object
# - ex_ids (list[str]):
# - df (pd.DataFrame): dataframe containing examples
# - id_col (str): name of df column with unique IDs
# - in_text_col (str): name of df column with input text
# - out_text_col (str): name of df column with output text
# - score (int): score to assign to these examples (0 or 1)
# - source (str): source of the score (optional)
# - score_col (str): name of df column with example scores
# - source_col (str): name of df column with score sources
def ex_ids_to_dataset(
    ex_ids,
    df,
    id_col,
    in_text_col,
    out_text_col,
    score,
    source,
    score_col="score",
    source_col="source",
):
    ex_rows = [
        [
            ex_id,
            get_ex_col(df, ex_id, id_col=id_col, col=in_text_col),
            get_ex_col(df, ex_id, id_col=id_col, col=out_text_col),
            score,
            source,
        ]
        for ex_id in ex_ids
    ]
    cols = [
        id_col,
        in_text_col,
        out_text_col,
        score_col,
        source_col,
    ]
    ex_df = pd.DataFrame(ex_rows, columns=cols)
    examples = Dataset(
        df=ex_df,
        id_col=id_col,
        in_text_col=in_text_col,
        out_text_col=out_text_col,
        score_col=score_col,
        source_col=source_col,
    )
    return examples
