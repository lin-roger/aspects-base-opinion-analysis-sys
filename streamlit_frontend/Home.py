from functools import partial
from elasticsearch import Elasticsearch, helpers
from glom import glom, Coalesce
from collections import Counter
from itertools import chain

import numpy as np
from sentiment import SentimentVisualizer
from dtm import DTModelVisualizer
from streamlit_echarts import st_pyecharts

import streamlit as st
import eland as ed
import pandas as pd
import yaml
import datetime
import pickle

st.set_page_config(
    page_title="社群輿情追蹤系統",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

with open("config.yaml", "r") as stream:
    config = yaml.safe_load(stream)


@st.cache_resource
def load_n_gram_model():
    with open("model_persistent/n_gram_model/n_gram.pickle", "rb") as f:
        n_gram_model = pickle.load(f)
    return n_gram_model


@st.cache_resource
def init_connection():
    # return Elasticsearch("http://host.docker.internal:9200", verify_certs=False, basic_auth=("elastic", "123456"))
    return Elasticsearch(
        "http://elasticsearch:9200",
        verify_certs=False,
        basic_auth=("elastic", "123456"),
    )


@st.cache_data(ttl=600)
def query_from_es(
    query_words: str,
    query_range: tuple[datetime.date, datetime.date],
    selection: list[str],
    selection_broad: list[str],
    tern_seatch: bool,
):
    body = {
        "_source": [
            "title_aste.*",
            "context_aste.*",
            "date",
            "comments.content_aste.*",
            "context_token",
            "context_tag",
            "context_vector",
        ],
        "query": {
            "bool": {
                "filter": [
                    {
                        "bool": {
                            "should": [],
                        }
                    },
                    {"terms": {"platform": selection}},
                    {"terms": {"borad": selection_broad}},
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
    if tern_seatch:
        query_words = query_words.split()
        body["query"]["bool"]["filter"][0]["bool"]["should"] = [
            {
                "terms_set": {
                    "title_token.keyword": {
                        "terms": query_words,
                        "minimum_should_match_script": {"source": "params.num_terms"},
                    }
                }
            },
            {
                "terms_set": {
                    "context_token.keyword": {
                        "terms": query_words,
                        "minimum_should_match_script": {"source": "params.num_terms"},
                    }
                }
            },
        ]
    else:
        body["query"]["bool"]["filter"][0]["bool"]["should"] = [
            {
                "multi_match": {
                    "query": " ".join(query_words),
                    "fields": ["title", "context"],
                    "minimum_should_match": "3<75%",
                }
            }
        ]

    res = list(
        helpers.scan(
            st.session_state.es, query=body, index=st.session_state.index, size=5000
        )
    )

    return res


def n_gram_recommend(searchterm: str) -> list:
    if not searchterm:
        return []
    terms = searchterm.split()
    commends = n_gram_model[terms].most_common(5)
    return [commend[0] for commend in commends]


def set_query_word(query_word, idx):
    st.session_state.query_word[idx] += " " + query_word


def submit(**kwargs):
    kwargs["query_word"] = [i for i in kwargs["query_word"] if i]

    st.session_state.show_search_result = True
    st.session_state.query_output = kwargs

# {
#         "tern_seatch": tern_seatch,
#         "query_word": st.session_state.query_word[:number],
#         "query_range": query_range,
#         "selection": selection,
#         "selection_broad": selection_broad,
#     },


def visual_doc(list_doc: pd.DataFrame):
    tabs = st.tabs(list_doc.index.to_list())
    for i, (_, ids) in enumerate(list_doc.iterrows()):
        ids = np.concatenate(ids.to_list()).tolist()
        ed_data = ed.DataFrame(
            st.session_state.es,
            st.session_state.index,
            columns=["title", "platform", "borad", "date", "link"],
        )
        with tabs[i]:
            tmp = ed_data.es_query({"query": {"ids": {"values": ids}}})
            if not tmp.empty:
                pd_data = ed.eland_to_pandas(tmp)
                st.dataframe(
                    pd_data,
                    hide_index=True,
                    use_container_width=True,
                    column_config={"link": st.column_config.LinkColumn()},
                )


def ids2doc(ids: list):
    ed_data = ed.DataFrame(
        st.session_state.es,
        st.session_state.index,
        columns=["title", "platform", "borad", "date", "link"],
    )
    tmp = ed_data.es_query({"query": {"ids": {"values": ids}}})
    if not tmp.empty:
        pd_data = ed.eland_to_pandas(tmp)
        return pd_data
    return None


# def sentiment_analysis_pie_chart():
#     pass


# def sentiment_analysis_sankey_chart():
#     pass


@st.cache_data(ttl=600)
def topic_modeling_line_chart(res_list, q_word: list[str]):
    dtm_visual = DTModelVisualizer(res_list, q_word)
    dtm_figs = dtm_visual.visual_topic_models()
    return dtm_figs


n_gram_model = load_n_gram_model()
max_value = 4

if "query_word" not in st.session_state:
    st.session_state.query_word = [""] * max_value
# if "query_range" not in st.session_state:
#     st.session_state.query_range = None
if "es" not in st.session_state:
    st.session_state.es = init_connection()
if "index" not in st.session_state:
    st.session_state.index = config["index"]
if "allow_pos" not in st.session_state:
    st.session_state.allow_pos = set(config["allow_pos"])
# if "tern_seatch" not in st.session_state:
#     st.session_state.tern_seatch = True
if "show_search_result" not in st.session_state:
    st.session_state.show_search_result = False

# [功能介紹](#功能介紹)
st.sidebar.markdown(
    """
# 社群輿情追蹤系統 💬
- [情感分析](#情感分析)
- [主題趨勢](#主題趨勢)
""",
    unsafe_allow_html=True,
)

st.title("社群輿情追蹤系統 💬")
st.caption("快速追綜不同輿情趨勢")
# st.header("功能介紹")
# st.markdown(
#     """- DTM(動態主題模型): 將討論特定關鍵字之輿論的主題變化趨勢可視化。
# - ABSA(方面情感分析): 將討論特定關鍵字之輿論的情感變化趨勢可視化，並解析其情感極性之組成因素。"""
# )

# %%
with st.container(key="search_form", border=True):
    tern_seatch = st.toggle("Term Search", value=True)
    selection = st.segmented_control(
        "資料來源",
        options=config["platforms"].keys(),
        default=config["platforms"].keys(),
        selection_mode="multi",
    )
    options_broad = [
        category
        for platform in selection
        for category in config["platforms"][platform]["boards"]
    ]
    selection_broad = st.multiselect("選擇類別", options_broad, options_broad)

    l_col, r_col = st.columns([7, 3])
    with l_col:
        today = datetime.datetime.now()
        last_month = today - datetime.timedelta(days=30)
        query_range = st.date_input(
            "查詢時間範圍",
            value=(last_month, today),
            format="YYYY/MM/DD",
            # label_visibility="collapsed",
        )

    with r_col:
        number = st.number_input(
            "比較欄位", min_value=1, max_value=max_value, value=1, step=1
        )

    cols = st.columns(number)
    for idx, col in enumerate(cols):
        with col:
            # with st.container(border=True):
            st.session_state.query_word[idx] = st.text_input(
                f"關鍵字{idx+1}",
                st.session_state.query_word[idx],
                # label_visibility="collapsed",
                placeholder="輸入關鍵字",
                key=f"query_word_{idx}",
            )
            tmp = n_gram_recommend(st.session_state.query_word[idx])
            if len(tmp) != 0:
                with st.expander("推薦關鍵字"):
                    for h in tmp:
                        st.button(
                            h,
                            use_container_width=True,
                            on_click=partial(set_query_word, h, idx),
                            key=f"commend_{idx}_{h}",
                        )
    st.button(
        "查詢",
        on_click=submit,
        kwargs={
            "tern_seatch": tern_seatch,
            "query_word": st.session_state.query_word[:number],
            "query_range": query_range,
            "selection": selection,
            "selection_broad": selection_broad,
        },
    )


if st.session_state.show_search_result:
    q_range = st.session_state.query_output["query_range"]
    plats = st.session_state.query_output["selection"]
    bords = st.session_state.query_output["selection_broad"]
    t_seatch = st.session_state.query_output["tern_seatch"]
    res_list = [
        query_from_es(q, q_range, plats, bords, t_seatch)
        for q in st.session_state.query_output["query_word"]
    ]
    # st.write(res_list)

    sa_visualizer = SentimentVisualizer(
        res_list, st.session_state.query_output["query_word"]
    )
    st.header("情感分析", anchor="情感分析")
    sa_line_chat, date_id_df = sa_visualizer.sentiment_analysis_line_chart()
    select_day = st_pyecharts(
        sa_line_chat,
        events={
            "click": "function(params) {console.log(params.data[0]); return params.data[0]}",
            "brushEnd": "function(params) {return params.areas[0].coordRange}",
        },
    )

    sun_figs = sa_visualizer.sentiment_analysis_word_cloud(select_day)
    col = st.columns(len(sun_figs))
    for i, fig in enumerate(sun_figs):
        with col[i]:
            st_pyecharts(fig)

    if len(st.session_state.query_output["query_word"]) >= 2:

        options = st.session_state.query_output["query_word"].copy()
        l_selection = st.pills(
            "### Left", options, selection_mode="single", default=options[0]
        )
        options.remove(l_selection)
        r_selection = st.pills(
            "### Right",
            options,
            selection_mode="single",
            default=options[0],
        )

        if l_selection and r_selection:
            sankey_chat_col, sankey_df_col = st.columns(2)
            sankey_chat, sankey_df = sa_visualizer.sentiment_analysis_sankey_charts(
                st.session_state.query_output["query_word"].index(l_selection),
                st.session_state.query_output["query_word"].index(r_selection),
                select_day,
            )
            with sankey_chat_col:
                select_rel = {}
                select_rel = st_pyecharts(
                    sankey_chat,
                    height="800px",
                    events={
                        "click": "function(params) {console.log(params); return params.data}"
                    },
                )
            if select_rel:
                if "value" in select_rel.keys():
                    source = select_rel["source"].split(".")[-1]
                    l_felid = "o"
                    if source in ["POS", "NEG", "NAT"]:
                        l_felid = "t"

                    target = select_rel["target"].split(".")[-1]
                    r_felid = "o"
                    if target in ["POS", "NEG", "NAT"]:
                        r_felid = "t"
                    ids = (
                        sankey_df.query(
                            f"{l_felid}_left == '{source}' & {r_felid}_right == '{target}'"
                        )["id"]
                        .unique()
                        .tolist()
                    )
                    with sankey_df_col:
                        st.dataframe(
                            ids2doc(ids),
                            hide_index=True,
                            use_container_width=True,
                            column_config={"link": st.column_config.LinkColumn()},
                        )

    if isinstance(select_day, str):
        # st.dataframe(date_id_df.loc[select_day].to_frame())
        visual_doc(date_id_df.loc[select_day].to_frame())
    elif isinstance(select_day, list):
        select_day = [str(datetime.date.fromtimestamp(i / 1000)) for i in select_day]
        # st.dataframe(date_id_df.loc[select_day[0]:select_day[1]].T)
        visual_doc(date_id_df.loc[select_day[0] : select_day[1]].T)

    st.header("主題趨勢", anchor="主題趨勢")
    dtm_figs = topic_modeling_line_chart(
        res_list, st.session_state.query_output["query_word"]
    )
    col = st.columns(len(dtm_figs))
    for i, fig in enumerate(dtm_figs):
        with col[i]:
            st.plotly_chart(fig)
