from functools import partial
from elasticsearch import Elasticsearch

import streamlit as st
import yaml
import datetime


with open("config.yaml", "r") as stream:
    config = yaml.safe_load(stream)

st.set_page_config(
    page_title="社群輿情追蹤系統",
    page_icon="💬",
)


@st.cache_resource
def init_connection():
    # return Elasticsearch("http://host.docker.internal:9200", verify_certs=False, basic_auth=("elastic", "123456"))
    return Elasticsearch(
        "http://elasticsearch:9200",
        verify_certs=False,
        basic_auth=("elastic", "123456"),
    )


def set_query_word(x):
    if x != "":
        st.session_state.query_word = x


def set_query_range(x):
    st.session_state.query_range = x


if "query_word" not in st.session_state:
    st.session_state.query_word = ""
if "query_range" not in st.session_state:
    st.session_state.query_range = None
if "es" not in st.session_state:
    st.session_state.es = init_connection()
if "index" not in st.session_state:
    st.session_state.index = config["index"]
if "allow_pos" not in st.session_state:
    st.session_state.allow_pos = set(config["allow_pos"])
if "tern_seatch" not in st.session_state:
    st.session_state.tern_seatch = True

st.sidebar.header("Home")
st.write("# 社群輿情追蹤系統 💬")
st.markdown(
    """
快速追綜不同輿情趨勢\n
## 功能
- DTM(動態主題模型): 將討論特定關鍵字之輿論的主題變化趨勢可視化。
- ABSA(方面情感分析): 將討論特定關鍵字之輿論的情感變化趨勢可視化，並解析其情感極性之組成因素。
## 近期熱門關鍵字
"""
)

hito = ["台積電", "台灣", "疫苗", "美國", "中國"]
col = st.columns(len(hito))
for h, c in zip(hito, col):
    with c:
        st.button(h, on_click=partial(set_query_word, h))

set_query_word(st.text_input("輸入查詢關鍵字", st.session_state.query_word))
# st.write(f"查詢關鍵字: {st.session_state.query_word}")

today = datetime.datetime.now()
last_month = today - datetime.timedelta(days=30)

set_query_range(
    st.date_input(
        "查詢時間範圍",
        value=(last_month, today),
        format="YYYY/MM/DD",
    )
)

st.session_state.tern_seatch = st.toggle("Term Search", st.session_state.tern_seatch)