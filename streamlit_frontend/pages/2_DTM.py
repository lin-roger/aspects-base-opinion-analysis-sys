# from streamlit_echarts import st_echarts
from calendar import c
from glom import glom
from bertopic import BERTopic
from elasticsearch import helpers
from collections import Counter

# from sklearn.feature_extraction.text import CountVectorizer
# from umap import UMAP


import streamlit as st
import pandas as pd
import numpy as np

query_word = st.session_state.query_word
query_range = st.session_state.query_range
es = st.session_state.es
index = st.session_state.index
topic_model = BERTopic.load("model_persistent/topics_model")


def tag_filter_by_pos(tag_list, pos_list):
    if not tag_list:
        return ""
    cleaned_tag_list = [
        tag for tag, pos in zip(tag_list, pos_list) if pos in st.session_state.allow_pos
    ]
    return " ".join(cleaned_tag_list)


@st.cache_data(ttl=600, max_entries=10)
def query_vec(query_word, query_range):
    if st.session_state.tern_seatch:
        body = {
            "_source": ["context_token", "context_tag", "context_vector", "date"],
            "query": {
                "bool": {
                    "filter": [
                        {
                            "bool": {
                                "should": [
                                    {"term": {"title_token.keyword": query_word}},
                                    {"term": {"context_token.keyword": query_word}},
                                ],
                            }
                        },
                        {
                            "range": {
                                "date": {
                                    "gte": query_range[0].isoformat(),
                                    "lte": query_range[1].isoformat(),
                                    "time_zone": "+08:00",
                                    "format": "yyyy-MM-dd",
                                },
                            }
                        },
                    ]
                }
            },
        }
    else:
        body = {
            # "_source": ["title", "title_vector", "context", "context_vector", "date"],
            "_source": ["context_token", "context_tag", "context_vector", "date"],
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query_word,
                                "fields": ["title", "context"],
                                "minimum_should_match": "50%",
                            }
                        },
                        {
                            "range": {
                                "date": {
                                    "gte": query_range[0].isoformat(),
                                    "lte": query_range[1].isoformat(),
                                    "time_zone": "+08:00",
                                    "format": "yyyy-MM-dd",
                                },
                            }
                        },
                    ]
                }
            },
        }
    res = list(
        helpers.scan(
            es,
            query=body,
            index=index,
            size=5000,
        )
    )
    assert len(res) != 0
    vec_df = pd.DataFrame.from_dict(glom(res, "*._source"))
    vec_df = vec_df[
        vec_df["context_token"].apply(lambda x: x is not None)
        & vec_df["context_vector"].apply(lambda x: isinstance(x, list))
    ]
    vec_df["text"] = vec_df.apply(
        lambda x: tag_filter_by_pos(x["context_token"], x["context_tag"]), axis=1
    )
    return vec_df


def fit_topic_model(vec_df):
    docs = vec_df["text"].tolist()
    vecs = np.array(vec_df["context_vector"].tolist())
    timestamps = vec_df["date"].apply(lambda x: x[:10]).tolist()
    # timestamps = vec_df["date"].tolist()

    topics, _ = topic_model.transform(docs, vecs)
    counter = Counter(topics)
    # st.write(counter.most_common(10))
    # topics_over_time = topic_model.topics_over_time(
    #     docs=docs, topics=topics.tolist(), timestamps=timestamps, datetime_format="%Y-%m-%d %H:%M:%S.%f"
    # )
    topics_over_time = topic_model.topics_over_time(
        docs=docs,
        topics=topics.tolist(),
        timestamps=timestamps,
        datetime_format="%Y-%m-%d",
        global_tuning=False,
    )
    
    return topics_over_time, counter


@st.cache_data(ttl=600, max_entries=10)
def gen_dtm():
    vec_df = query_vec(query_word, query_range)
    topics_over_time_df, counter = fit_topic_model(vec_df)
    return topic_model.visualize_topics_over_time(topics_over_time_df, topics = [x[0] for x in counter.most_common(10)])


st.sidebar.header("DTM")
st.write("# DTM 💬")
st.write(f"## 「{query_word}」 的主題趨勢")
st.plotly_chart(gen_dtm())  # Same as st.write(df)

# TODO: 圖表美化，改用echarts
# value = st_echarts(option, events=e, height="600px")
# st.write(value)
# print(value)
