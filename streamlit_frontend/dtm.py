from collections import Counter
from bertopic import BERTopic
from glom import glom
from pyecharts.charts import Line
import pyecharts.options as opts


import numpy as np
import streamlit as st
import eland as ed
import pandas as pd


topic_model = BERTopic.load("model_persistent/topics_model")


class DTModelVisualizer:
    def __init__(self, res_list, query_word: list[str]):
        self.df_list = [self._res2vec_df(res) for res in res_list]
        self.query_word = query_word

    def _tag_filter_by_pos(self, tag_list, pos_list):
        if not tag_list:
            return ""
        cleaned_tag_list = [
            tag
            for tag, pos in zip(tag_list, pos_list)
            if pos in st.session_state.allow_pos
        ]
        return " ".join(cleaned_tag_list)

    def _res2vec_df(self, res):
        vec_df = pd.DataFrame.from_dict(glom(res, "*._source"))
        vec_df = vec_df[
            vec_df["context_token"].apply(lambda x: x is not None)
            & vec_df["context_vector"].apply(lambda x: isinstance(x, list))
        ]
        vec_df["text"] = vec_df.apply(
            lambda x: self._tag_filter_by_pos(x["context_token"], x["context_tag"]),
            axis=1,
        )
        return vec_df

    def _fit_topic_model(self, vec_df):
        docs = vec_df["text"].tolist()
        vecs = np.array(vec_df["context_vector"].tolist())
        timestamps = vec_df["date"].apply(lambda x: x[:10]).tolist()

        topics, _ = topic_model.transform(docs, vecs)
        counter = Counter(topics)
        topics_over_time = topic_model.topics_over_time(
            docs=docs,
            topics=topics.tolist(),
            timestamps=timestamps,
            datetime_format="%Y-%m-%d",
            global_tuning=False,
        )
        return topics_over_time, counter
    
    def visual_topic_models(self):
        figs = []
        for _, df in enumerate(self.df_list):
            topics_over_time, counter = self._fit_topic_model(df)
            fig = topic_model.visualize_topics_over_time(
                topics_over_time, topics=[x[0] for x in counter.most_common(10)]
            )
            fig = fig.update_traces({"line_shape": "spline", "mode": "lines+markers"})
            fig = fig.update_layout({"title": ""})
            fig = fig.update_layout(legend=dict(
                orientation="h",
                yanchor="bottom",
                xanchor="left",
                y = 1.02,
            ))
            figs.append(fig)
        return figs