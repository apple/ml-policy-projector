"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

# Dataset
import pandas as pd
from typing import List, Optional

# Constants for use in external json spec
ID = "id"
IN_TEXT = "in_text"
OUT_TEXT = "out_text"
SOURCE = "source"
SCORE = "score"


class Dataset:

    # Dataset setup
    # - df (pd.DataFrame): dataframe to store
    # - id_col (str): name of df column with unique IDs
    # - in_text_col (str): name of df column with *input* text to analyze
    # - out_text_col (str): name of df column with *output* text to analyze
    # - score_col (str): name of df column with existing concept scores
    # - source_col (str): name of df column with score source ("manual" or "auto")
    # - cols (List[str]): (optional) list of columns from df to include (Default is all of the above columns)
    def __init__(
        self,
        df: pd.DataFrame,
        id_col: str,
        in_text_col: str,
        out_text_col: str,
        score_col: str,
        source_col: str,
        cols: Optional[List[str]] = None,
    ):
        self.id_col = id_col
        self.in_text_col = in_text_col
        self.out_text_col = out_text_col
        self.score_col = score_col
        self.source_col = source_col

        if cols is None:
            self.cols = [
                self.in_text_col,
                self.out_text_col,
                self.score_col,
                self.id_col,
                self.source_col,
            ]
        else:
            self.cols = cols

        self.text_cols = [self.in_text_col, self.out_text_col]
        self.cols_to_json_cols = {
            self.id_col: ID,
            self.in_text_col: IN_TEXT,
            self.out_text_col: OUT_TEXT,
            self.source_col: SOURCE,
            self.score_col: SCORE,
        }
        self.json_cols = list(self.cols_to_json_cols.keys())

        self.data = df[self.cols]  # Source of truth on the data

    # Get the specified column from the dataframe
    def get(self, col_name):
        return self.data[col_name]

    # Update the data with the provided id with the provided value at the indicated column
    def update(self, ex_id, col_name, val):
        updated_df = self.data.copy()
        updated_df.loc[updated_df[self.id_col] == ex_id, col_name] = val
        self.data = updated_df

    # Return the total number of items in the dataset
    def count(self):
        return len(self.data)

    # Return the dataset as a dataframe with the specified columns (or default columns if not provided)
    def to_df(self, cols: Optional[List[str]] = None):
        if cols is None:
            cols = self.cols
        return self.data[cols]

    # Convert the dataset to JSON spec
    def to_json(self):
        df = self.data[self.json_cols]
        df = df.rename(columns=self.cols_to_json_cols)
        return df.to_dict("records")

    # Convert from a JSON spec to an object
    @staticmethod
    def from_json(spec):
        if spec is None:
            return None
        df = pd.DataFrame(spec)
        return Dataset(
            df=df,
            id_col=ID,
            in_text_col=IN_TEXT,
            out_text_col=OUT_TEXT,
            score_col=SCORE,
            source_col=SOURCE,
        )

    # Given another Dataset, adds its data to the current Dataset
    def add(self, data_to_add):
        col_names = ["id_col", "in_text_col", "out_text_col", "score_col", "source_col"]
        col_mapping = {
            getattr(data_to_add, col): getattr(self, col) for col in col_names
        }
        df_to_add = data_to_add.data.copy()
        df_to_add = df_to_add.rename(columns=col_mapping)
        df_to_add = df_to_add[self.cols]

        cur_ids = self.data[self.id_col].unique().tolist()
        df_to_add = df_to_add[
            ~df_to_add[self.id_col].isin(cur_ids)
        ]  # Remove rows already in df
        self.data = pd.concat([self.data, df_to_add], ignore_index=True)

    # Join provided Dataset objects on their respective id columns
    # - d1 (Dataset): Left dataset to join
    # - d2 (Dataset): Right dataset to join
    # - cols1 (List[str]): subset of columns to include from d1
    # - cols2 (List[str]): subset of columns to include from d2
    # - how (str): type of merge to perform (default: inner)
    @staticmethod
    def join(
        d1,
        d2,
        cols1: Optional[List[str]] = None,
        cols2: Optional[List[str]] = None,
        how: str = "inner",
    ):
        df1 = d1.to_df(cols1)
        df2 = d2.to_df(cols2)
        df_merged = df1.merge(df2, how=how, left_on=d1.id_col, right_on=d2.id_col)
        return df_merged
