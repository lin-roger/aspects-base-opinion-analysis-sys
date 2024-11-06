from streamlit_echarts import st_echarts
from glom import glom
from bertopic import BERTopic
from elasticsearch import helpers
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP


import streamlit as st
import pandas as pd
import numpy as np

query_word = st.session_state.query_word
es = st.session_state.es
index = st.session_state.index

@st.cache_data(ttl=600, max_entries=10)
def query_vec(query_word):
    body = {
        "_source": ["title", "title_vector", "context", "context_vector", "date"],
        "query": {
            "multi_match": {
                "query": query_word,
                "fields": ["title", "context"],
                "minimum_should_match": "50%",
            },
        },
    }
    res = list(
        helpers.scan(
            es,
            query=body,
            index=index,
        )
    )
    assert len(res) != 0
    vec_df = pd.DataFrame.from_dict(glom(res, "*._source"))
    return vec_df


def init_topic_model(num_of_docs: int):
    def tokenize_zh(text: str):
        tokens = es.indices.analyze(
            index="dcard", analyzer="ik_smart", text=text
        ).body
        tokens = glom(tokens, "tokens.*.token")
        return tokens

    n_components = 5
    umap_model = UMAP(
        n_neighbors=max(
            2, round(num_of_docs * 0.2)
        ),  # n_neighbors must be greater than 1
        n_components=n_components,
        min_dist=0.0,
        metric="cosine",
        init=(
            "spectral" if num_of_docs > n_components + 1 else "random"
        ),  # lmcinnes umap issue #201
    )

    topic_model = BERTopic(
        language="chinese",
        umap_model=umap_model,
        vectorizer_model=CountVectorizer(tokenizer=tokenize_zh),
        min_topic_size=max(
            2, round(num_of_docs * 0.05)
        ),  # Min cluster size must be greater than one
    )
    return topic_model


def fit_topic_model(vec_df):
    docs = vec_df["context"].tolist()
    embeddings = np.array(vec_df["context_vector"].tolist())
    timestamps = vec_df["date"].tolist()

    topic_model = init_topic_model(len(docs))
    topic_model.fit(docs, embeddings)
    topics_over_time = topic_model.topics_over_time(
        docs, timestamps, nr_bins=20, datetime_format="%Y-%m-%d %H:%M:%S.%f"
    )

    return topic_model, topics_over_time


@st.cache_data(ttl=600, max_entries=10)
def gen_dtm(query_word):
    vec_df = query_vec(query_word)
    _, topics_over_time_df = fit_topic_model(vec_df)
    return topics_over_time_df


st.sidebar.header("DTM")
st.write("# DTM 💬")
st.write(f"## *{query_word}* 的主題趨勢")
st.dataframe(gen_dtm(query_word))  # Same as st.write(df)


# value = st_echarts(option, events=e, height="600px")
# st.write(value)
# print(value)
