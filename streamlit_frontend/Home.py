import streamlit as st
from functools import partial
from elasticsearch import Elasticsearch, helpers


st.set_page_config(
        page_title="社群輿情追蹤系統",
        page_icon="💬",
    )

@st.cache_resource
def init_connection():
    # return Elasticsearch(
    # "https://elasticsearch:9200",
    # api_key="YjVwMHpKSUI1aVdrRE5nRHhQN0o6UkxLTGRoUGRSVDZic3NCU2IzNFVnQQ==",
    # verify_certs=False,
    # return Elasticsearch("http://host.docker.internal:9200", verify_certs=False, basic_auth=("elastic", "123456"))
    return Elasticsearch("http://elasticsearch:9200", verify_certs=False, basic_auth=("elastic", "123456"))
       
def set_query_word(x):
    if x!="":
        st.session_state.query_word = x
        # print(x)

if 'query_word' not in st.session_state:
    st.session_state.query_word = ''
if 'es' not in st.session_state:
    st.session_state.es = init_connection()

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
# for h in hito:
    with c:
        st.button(h, on_click=partial(set_query_word, h))

set_query_word(st.text_input("輸入查詢關鍵字", st.session_state.query_word))
st.write(f"查詢關鍵字: {st.session_state.query_word}")
    

# def dtm():
#     import streamlit as st

#     st.write("# DTM 💬")

# def absa():
#     import streamlit as st
    
#     st.write("# ABSA 💬")



# page_names_to_funcs = {
#     "home": intro,
#     "DTM": dtm,
#     "ABSA": absa,
# }


