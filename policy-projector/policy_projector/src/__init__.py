"""
For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

import importlib.metadata
import pathlib

import anywidget
import traitlets
import util

from dataset import Dataset

try:
    __version__ = importlib.metadata.version("policy_projector")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

_DEV = True  # switch to False for production

if _DEV:
    # from `npx vite`
    ESM = "http://localhost:5173/widget/index.js?anywidget"
    CSS = ""
else:
    # from `npm run build`
    # Path to static from policy_projector/src (the python package)
    bundled_assets_dir = pathlib.Path(__file__).parent.parent / "static"
    ESM = (bundled_assets_dir / "index.js").read_text()
    CSS = (bundled_assets_dir / "index.css").read_text()


"""
Widget for viewing concepts or policies and their associated data + metadata
"""


class TableWidget(anywidget.AnyWidget):
    _esm = ESM
    _css = CSS
    name = traitlets.Unicode().tag(sync=True)
    id = traitlets.Any().tag(sync=True)
    col_settings = traitlets.List([]).tag(sync=True)
    col_types = traitlets.List([]).tag(sync=True)
    metadata = traitlets.Dict({}).tag(sync=True)
    rows = traitlets.List([]).tag(sync=True)
    rows_updated = traitlets.List([]).tag(sync=True)
    save_table = traitlets.Bool(False).tag(sync=True)

    @staticmethod
    def get_col_settings(cols_to_show, text_cols, score_col, editable_cols):
        if (score_col is not None) and (score_col not in editable_cols):
            editable_cols.append(score_col)

        def get_width(col):
            if col in text_cols:
                return "400px"
            return "100px"

        def get_col_type(col):
            if col in text_cols:
                return "Text"
            elif col == score_col:
                return "Score"
            else:
                return "Text"

        col_settings = [
            {
                "headerName": col,
                "cellStyle": {
                    "width": get_width(col),
                },
                "defaultColumnTypeName": get_col_type(col),
                "isCellTextEditable": (True if col in editable_cols else False),
            }
            for col in cols_to_show
        ]
        return col_settings

    @staticmethod
    def get_col_types(pos_label, neg_label):
        change_text_func = """ 
            (cellText) => {{
                if (cellText === '0') {{
                    return "{neg}"; 
                }} else if (cellText === '1')  {{ 
                    return "{pos}";
                }} else {{
                    return cellText;
                }}
            }}
        """.format(
            pos=pos_label, neg=neg_label
        )
        change_style_func = """ 
            (cellText) => {{
                if (cellText === "{neg}") {{
                    return {{ backgroundColor: 'white' }};
                }} else if (cellText === "{pos}")  {{
                    return {{ backgroundColor: '#9cd09c' }};
                }}
            }}
        """.format(
            pos=pos_label, neg=neg_label
        )
        col_types = [
            {
                "name": "Score",
                "select": {
                    "options": [pos_label, neg_label],
                    "canAddMoreOptions": False,
                },
                "iconSettings": {"resusableIconName": "select"},
                "customTextProcessing": {
                    "changeTextFunc": change_text_func,
                    "changeStyleFunc": change_style_func,
                },
            }
        ]
        return col_types

    def __init__(
        self,
        obj,
        obj_type,
        dataset,
        cols_to_show,
        text_cols=[],
        score_col=None,
        edit_type=None,
        editable_cols=[],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.obj = obj
        self.obj_type = obj_type
        self.edit_type = edit_type
        self.dataset = dataset
        self.name = f"{self.obj_type}: {self.obj.name}"
        self.id = self.obj.id
        self.score_col = score_col
        self.pos_label = "1: Match"
        self.neg_label = "0: Non-match"

        # Prepare widget view
        self.df = self.dataset.to_df(cols=cols_to_show)
        df_rows = util.df_to_rows(self.df, cols_to_show)
        self.rows = df_rows
        self.rows_updated = df_rows
        self.save_table = False

        # Column settings
        self.col_settings = TableWidget.get_col_settings(
            cols_to_show, text_cols, score_col, editable_cols
        )
        self.col_types = TableWidget.get_col_types(self.pos_label, self.neg_label)

        # Metadata
        # Map from <human-readable name for frontend> to <name of internal object attribute>
        if self.obj_type == "Concept":
            self.metadata_keys = {
                "Description": "description",
            }
        elif self.obj_type == "Policy":
            self.metadata_keys = {
                "Description": "description",
                "IF these concepts apply": "if_concept_names",
                "THEN mitigate this concept": "then_actions",
            }

        self.metadata = {k: getattr(self.obj, v) for k, v in self.metadata_keys.items()}

    @traitlets.observe("rows_updated")
    def _observe_rows(self, change):
        # Update internal df to match changes from widget
        update = change["new"]
        if len(update) > 0:
            self.df = util.rows_to_df(update)

    @traitlets.observe("metadata")
    def _observe_metadata(self, change):
        update = change["new"]
        for k, v in update.items():
            setattr(self.obj, self.metadata_keys[k], v)

    @traitlets.observe("save_table")
    def _observe_save_table(self, change):
        if self.save_table:
            if self.edit_type == "Example":
                cur_example_ids = self.obj.examples
                # Filter to examples with positive label
                new_df = self.df[self.df[self.score_col] == self.pos_label]
                if len(new_df) > 0:
                    new_example_ids = new_df[self.dataset.id_col].tolist()
                    cur_example_ids.extend(new_example_ids)
                    self.obj.examples = cur_example_ids
            # elif self.edit_type == "Fix":
            #     dataset_to_update = self.obj.fixes
            #     # Change the fix column to the output text column
            #     new_df = self.df.copy()
            #     new_df = new_df.drop(columns=[self.dataset.out_text_col])
            #     new_df = new_df.rename(columns={"fix": self.dataset.out_text_col})

            # new_examples = Dataset(
            #     df=new_df,
            #     id_col=self.dataset.id_col,
            #     in_text_col=self.dataset.in_text_col,
            #     out_text_col=self.dataset.out_text_col,
            #     score_col=self.dataset.score_col,
            #     source_col=self.dataset.source_col,
            # )
            # dataset_to_update.add(new_examples)
            self.save_table = False
