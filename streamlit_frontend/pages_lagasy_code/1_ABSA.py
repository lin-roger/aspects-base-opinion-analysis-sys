from streamlit_echarts import st_echarts
from elasticsearch import helpers
from collections import Counter
from itertools import chain
from glom import glom, Coalesce

import streamlit as st
import pandas as pd
import json


@st.cache_data(ttl=600, max_entries=10)
def query_absa(query_word, query_range):
    if st.session_state.tern_seatch:
        body = {
            "_source": [
                "title_aste.*",
                "context_aste.*",
                "date",
                "comments.content_aste.*",
            ],
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
            "_source": [
                "title_aste.*",
                "context_aste.*",
                "date",
                "comments.content_aste.*",
            ],
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
            st.session_state.es, query=body, index=st.session_state.index, size=5000
        )
    )
    assert len(res) != 0

    coalesce_of_path = Coalesce(
        "*._source.context_aste",
        "*._source.title_aste",
        "*._source.comments.*.content_aste",
    )

    aop_df = pd.DataFrame.from_dict(
        list(chain.from_iterable(glom(res, coalesce_of_path)))
    )
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


def generate_options(aspect):
    with open("template/absa_sunburst_template.json") as f:
        template = json.load(f)

    try:
        aop_df = query_absa(st.session_state.query_word, st.session_state.query_range)
    except AssertionError:
        st.write(f"## 找不到 *{st.session_state.query_word}*")
        return template

    template["series"]["data"] = aop_df_2_data(aop_df[aop_df.a == aspect])

    return template


def gen_wc_data():
    with open("template/absa_wc_template.json") as f:
        template = json.load(f)
    aop_df = query_absa(st.session_state.query_word, st.session_state.query_range)
    c = Counter(aop_df["a"].to_list()).items()

    template["series"]["data"] = [{"name": k, "value": v} for k, v in c]
    return template


st.sidebar.header("ABSA")
st.write("# ABSA 💬")
st.write(f"## 「{st.session_state.query_word}」相關文章的Aspects文字雲")
st.write("#### 點擊文字雲中的詞彙，查看該詞彙的情感分析結果")

data = gen_wc_data()

select = st_echarts(
    options=data,
    events={"click": "function(params) {return params.name}"},
    height="300px",
)

# TODO: o太多時，需要加其他類別替代

if select is not None:
    st.write(f"## 「{select}」之情感分析")
    st_echarts(
        options=generate_options(select),
        height="600px",
    )

# TODO: ABSA時間軸

# st.write(f"## *{st.session_state.query_word}* 的情感趨勢")
