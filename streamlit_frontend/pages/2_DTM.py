import streamlit as st
from streamlit_echarts import st_echarts
import numpy as np

if "dtm" not in st.session_state:
    st.session_state["dtm"] = np.random.rand(5, 7).tolist()

if "dtmIdx" not in st.session_state:
    st.session_state["dtmIdx"] = 0

st.sidebar.header("DTM")
st.write("# DTM 💬")
st.write(f"## *{st.session_state.query_word}* 的主題趨勢")

dList = ["05/23", "05/24", "05/25", "05/26", "05/27", "05/28"]

option = {
    "legend": {},
    "tooltip": {
      "trigger": 'axis',
      "showContent": "false"
    },
    "dataset": {
        "source": [
            ["Days"] + dList,
            ["topic_1"] + st.session_state["dtm"][0],
            ["topic_2"] + st.session_state["dtm"][1],
            ["topic_3"] + st.session_state["dtm"][2],
            ["topic_4"] + st.session_state["dtm"][3],
            ["topic_5"] + st.session_state["dtm"][4],
            # ["NAT", 40.1, 62.2, 69.5, 36.4, 45.2, 32.5],
        ]
    },
    "xAxis": { "type": 'category' },
    "yAxis": { "gridIndex": 0 },
    "grid": {"top": "55%"},
    "series": [
        {
            "emphasis": {"focus": "series"},
            "seriesLayoutBy": "row",
            "smooth": "true",
            "type": "line",
        }
    ]
    * len(st.session_state["dtm"])
    + [
        {
            "center": ["50%", "25%"],
            "emphasis": {"focus": "self"},
            "encode": {"itemName": "Days", "tooltip": dList[st.session_state["dtmIdx"]], "value": dList[st.session_state["dtmIdx"]]},
            "id": "pie",
            "label": {"formatter": "{b}: {@" + dList[st.session_state["dtmIdx"]] + "} ({d}%)"},
            "radius": "30%",
            "type": "pie",
        }
    ]
}

# e = {"updateAxisPointer": """
# function (event) {
#     const xAxisInfo = event.axesInfo[0];
#     if (xAxisInfo) {
#         const dimension = xAxisInfo.value + 1;
#         myChart.setOption({
#         series: {
#             id: 'pie',
#             label: {formatter: '{b}: {@[' + dimension + ']} ({d}%)'},
#             encode: {value: dimension, tooltip: dimension}}
#         });
#     }
# }
# """}

# e = {"updateAxisPointer": 'function(e){let t=e.dataIndex;if(t){let i=t+1;myChart.setOption({series:{id:"pie",label:{formatter:"{b}: {@["+i+"]} ({d}%)"},encode:{value:i,tooltip:i}}})}}'}
e = {"updateAxisPointer": "function(params) { return params; }"}

value = st_echarts(option, events=e, height="600px")
st.write(value)
print(value)
