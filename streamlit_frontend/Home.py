from functools import partial
from elasticsearch import Elasticsearch
from nltk.lm import NgramCounter
from streamlit_searchbox import st_searchbox
from st_keyup import st_keyup


import streamlit as st
import yaml
import datetime
import pickle

st.set_page_config(
    page_title="社群輿情追蹤系統",
    page_icon="💬",
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


def n_gram_recommend(searchterm: str) -> list:
    if not searchterm:
        return []
    terms = searchterm.split()
    commends = n_gram_model[terms].most_common(5)
    return [commend[0] for commend in commends]


def set_query_word(query_word, idx):
    st.session_state.query_word[idx] += " " + query_word


n_gram_model = load_n_gram_model()
max_value = 4

if "query_word" not in st.session_state:
    st.session_state.query_word = [""] * max_value
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


# st.sidebar.header("Home")
st.title("社群輿情追蹤系統 💬")
st.caption("快速追綜不同輿情趨勢")
st.header("功能介紹")
st.markdown(
    """- DTM(動態主題模型): 將討論特定關鍵字之輿論的主題變化趨勢可視化。
- ABSA(方面情感分析): 將討論特定關鍵字之輿論的情感變化趨勢可視化，並解析其情感極性之組成因素。"""
)

# %%
st.divider()
st.session_state.tern_seatch = st.toggle("Term Search", st.session_state.tern_seatch)

selection = st.segmented_control(
    "資料來源", config["platforms"].keys(), selection_mode="multi"
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
    st.session_state.query_range = st.date_input(
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
        with st.container(border=True):
            st.session_state.query_word[idx] = st.text_input(
                "輸入查詢關鍵字",
                st.session_state.query_word[idx],
                label_visibility="collapsed",
                key=f"query_word_{idx}",
            )
            tmp = n_gram_recommend(st.session_state.query_word[idx])
            if len(tmp) != 0:
                for h in tmp:
                    st.button(
                        h,
                        use_container_width=True,
                        on_click=partial(set_query_word, h, idx),
                    )

st.write(st.session_state.query_word[:number])
st.write(st.session_state.query_range)
st.write(selection)
st.write(selection_broad)
