from collections import Counter
from streamlit_echarts import st_echarts
from itertools import chain
from glom import glom
import streamlit as st
import pandas as pd
import json


@st.cache_data(ttl=600, max_entries=10)
def query_absa(query_word):
    body = {
        "_source": False,
        "query": {
            "nested": {
                "path": "context_aste",
                "query": {
                    "match": {
                        "context_aste.a": query_word,
                    }
                },
                "inner_hits": {},
            },
            "nested": {
                "path": "title_aste",
                "query": {
                    "match": {
                        "title_aste.a": query_word,
                    }
                },
                "inner_hits": {},
            },
            "nested": {
                "path": "comments.content_aste",
                "query": {
                    "match": {
                        "comments.content_aste.a": query_word,
                    }
                },
                "inner_hits": {},
            },
        },
    }
    res = st.session_state.es.search(
        index="dcard",
        body=body,
        filter_path=["hits.hits.inner_hits.*.hits.hits._source.*", "hits.total.value"],
    )

    # print(res)

    assert res.body["hits"]["total"]["value"] != 0
    aop_list = list(
        chain.from_iterable(glom(res.body, "hits.hits.**.hits.hits.*._source"))
    )
    aop_df = pd.DataFrame.from_dict(aop_list)
    aop_df["t"] = aop_df["p"].map(
        lambda x: "POS" if x >= 6 else "NAT" if x > 4 else "NEG"
    )
    return aop_df


def aop_df_2_data(aop_df):
    # print(aop_df)
    tag_counter = Counter(aop_df["t"])
    return [
        {
            "value": v,
            "name": k,
            "children": [
                {"value": c, "name": w}
                for w, c in Counter(aop_df.o[aop_df.t == k]).items()
            ],
        }
        for k, v in tag_counter.items()
    ]


def generate_options():
    with open("template/absa_template.json") as f:
        template = json.load(f)
    
    try:
        aop_df = query_absa(st.session_state.query_word)
    except AssertionError:
        st.write(f"## 找不到 *{st.session_state.query_word}*")
        return template
    
    template["series"]["data"] = aop_df_2_data(aop_df)

    return template


st.sidebar.header("ABSA")
st.write("# ABSA 💬")
st.write(f"## *{st.session_state.query_word}* 的情感組成")
st_echarts(
    options=generate_options(),
    height="600px",
)
# st.write(f"## *{st.session_state.query_word}* 的情感趨勢")
