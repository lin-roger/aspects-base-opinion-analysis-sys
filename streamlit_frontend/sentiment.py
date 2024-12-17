import datetime
from heapq import merge
from glom import glom, Coalesce
from itertools import chain
from pyecharts.charts import Line, Sunburst, Sankey, WordCloud
import pyecharts.options as opts
import pandas as pd
import streamlit as st


class SentimentVisualizer:
    def __init__(self, res_list, query_word: list[str]):
        self.df_list = [self._res2aop_df(res) for res in res_list]
        self.query_word = query_word

    def _res2aop_df(self, res):
        coalesce_of_path = Coalesce(
            "_source.context_aste",
            "_source.title_aste",
            "_source.comments.*.content_aste",
        )
        # st.write(res[:10])

        list_dict = []
        for i in res:
            try:
                g_tmp = glom(i, coalesce_of_path)
                if isinstance(g_tmp[0], list):
                    g_tmp = chain.from_iterable(g_tmp)
                for j in g_tmp:
                    list_dict.append(
                        {
                            "id": i["_id"],
                            "date": i["_source"]["date"],
                            "a": j["a"],
                            "o": j["o"],
                            "p": j["p"],
                        }
                    )
            except Exception as e:
                pass
                # st.write(e)
                # st.write(i)

        aop_df = pd.DataFrame.from_dict(list_dict)
        aop_df["date"] = aop_df["date"].astype("datetime64[ns]")
        aop_df["t"] = aop_df["p"].map(
            lambda x: "POS" if x >= 6 else "NAT" if x > 4 else "NEG"
        )
        return aop_df

    def _gen_sunburst_data(self, group_df):
        group_df = group_df["o"].value_counts().to_frame()
        data = []
        for p, o_df in group_df.groupby(level=0):
            o_df = o_df.loc[p]
            # st.write(o_df)
            o_df = pd.concat(
                [
                    o_df[:10],
                    pd.DataFrame([o_df[10:].sum()], index=["其他"], columns=["o"]),
                ]
            )

            data.append(
                opts.SunburstItem(
                    name=p,
                    # value=110,
                    children=[
                        opts.SunburstItem(name=o, value=int(num_of_o.iloc[0]))
                        # opts.SunburstItem(name=o, value=10)
                        for o, num_of_o in o_df.iterrows()
                    ],
                )
            )
        return data

    def _fileter_top_n(self, df, n=10, column="o"):
        select_o_aop_list = []
        for tag, df in df.groupby(["t"]):
            select_o = df[column].value_counts().head(n).index.tolist()
            select_o_aop_list.append(df.loc[df[column].isin(select_o)])
        return pd.concat(select_o_aop_list)

    def sentiment_analysis_sankey_charts(self, left_idx: int, right_idx: int, selected_date: str | list[str] = None):
        df_list = self.df_list
        if isinstance(selected_date, str):
            df_list = [
                df.set_index("date").loc[selected_date[:10]].reset_index()
                for df in self.df_list
            ]
        elif isinstance(selected_date, list):
            selected_date = [
                str(datetime.date.fromtimestamp(i / 1000)) for i in selected_date
            ]
            df_list = [
                df.set_index("date")
                .loc[selected_date[0] : selected_date[1]]
                .reset_index()
                for df in self.df_list
            ]
        
        left_df = self._fileter_top_n(df_list[left_idx])
        right_df = self._fileter_top_n(df_list[right_idx])
        merge_df = pd.merge(left_df, right_df, on="id", suffixes=("_left", "_right"))
        nodes = [
            *[
                {"name": f"{self.query_word[left_idx]}.{i}"}
                for i in merge_df["t_left"].unique().tolist()
            ],
            *[
                {"name": f"{self.query_word[right_idx]}.{i}"}
                for i in merge_df["t_right"].unique().tolist()
            ],
            *[
                {"name": f"{self.query_word[left_idx]}.{i}"}
                for i in merge_df["o_left"].unique().tolist()
            ],
            *[
                {"name": f"{self.query_word[right_idx]}.{i}"}
                for i in merge_df["o_right"].unique().tolist()
            ],
        ]

        links = [
            *[
                {
                    "source": f"{self.query_word[left_idx]}.{i}",
                    "target": f"{self.query_word[left_idx]}.{j}",
                    "value": v,
                }
                for (i, j), v in merge_df.groupby(["t_left", "o_left"]).size().items()
            ],
            *[
                {
                    "source": f"{self.query_word[left_idx]}.{i}",
                    "target": f"{self.query_word[right_idx]}.{j}",
                    "value": v,
                }
                for (i, j), v in merge_df.groupby(["o_left", "o_right"]).size().items()
            ],
            *[
                {
                    "source": f"{self.query_word[right_idx]}.{i}",
                    "target": f"{self.query_word[right_idx]}.{j}",
                    "value": v,
                }
                for (i, j), v in merge_df.groupby(["o_right", "t_right"]).size().items()
            ],
        ]

        # st.write(nodes)

        # st.write(merge_df.groupby(["t_left", "o_left"]).size())
        # st.write(merge_df.groupby(["o_left", "o_right"]).size())
        # st.write(merge_df.groupby(["o_right", "t_right"]).size())

        fig = (
            Sankey()
            .add(
                series_name="",
                nodes=nodes,
                links=links,
                emphasis_opts=opts.EmphasisOpts(focus="adjacency"),
                linestyle_opt=opts.LineStyleOpts(color="source", curve=0.5, opacity=0.5),
            )
            .set_global_opts(title_opts=opts.TitleOpts(title="情感流向"))
        )

        return fig, merge_df
    
    def sentiment_analysis_word_cloud(self, selected_date: str | list[str] = None):
        df_list = self.df_list
        if isinstance(selected_date, str):
            df_list = [
                df.set_index("date").loc[selected_date[:10]].reset_index()
                for df in self.df_list
            ]
        elif isinstance(selected_date, list):
            selected_date = [
                str(datetime.date.fromtimestamp(i / 1000)) for i in selected_date
            ]
            df_list = [
                df.set_index("date")
                .loc[selected_date[0] : selected_date[1]]
                .reset_index()
                for df in self.df_list
            ]
        
        o_word_freq = [
            df["o"].value_counts().head(100).to_dict() for df in df_list
        ]
        a_word_freq = [
            df["a"].value_counts().head(100).to_dict() for df in df_list
        ]
        
        figs = [
            WordCloud()
            .add(series_name="aspect", data_pair=[(k, v) for k, v in a_word_freq[i].items()])
            # .add(series_name="opinion", data_pair=[(k, v) for k, v in o_word_freq[i].items()])
            .set_global_opts(title_opts=opts.TitleOpts(title=f"{self.query_word[i]}"))
            for i in range(len(o_word_freq))
        ]
        return figs
            
        
                
        

    def sentiment_analysis_sunburst_charts(self, selected_date: str | list[str] = None):
        df_list = self.df_list
        if isinstance(selected_date, str):
            df_list = [
                df.set_index("date").loc[selected_date[:10]].reset_index()
                for df in self.df_list
            ]
        elif isinstance(selected_date, list):
            selected_date = [
                str(datetime.date.fromtimestamp(i / 1000)) for i in selected_date
            ]
            df_list = [
                df.set_index("date")
                .loc[selected_date[0] : selected_date[1]]
                .reset_index()
                for df in self.df_list
            ]

        group_list = [df.groupby("t") for df in df_list]
        datas = [self._gen_sunburst_data(group_df) for group_df in group_list]

        figs = [
            Sunburst()
            .add(
                series_name="",
                data_pair=data,
                label_layout_opts=opts.SunburstLabelLayoutOpts(is_hide_overlap=True),
                levels=[
                    {},
                    {},
                    {
                        "label": {"position": "outside", "padding": 1, "silent": False},
                    },
                ],
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{self.query_word[i]}"),
            )
            for i, data in enumerate(datas)
        ]

        return figs

    def sentiment_analysis_line_chart(self):
        group_list = [
            df.groupby(pd.Grouper(key="date", freq="D")) for df in self.df_list
        ]

        agg_df = pd.DataFrame([group["p"].mean().round(2) for group in group_list]).T
        agg_df.columns = self.query_word

        date_id_df = pd.concat(
            [group["id"].agg(["unique"]) for group in group_list], axis=1
        )
        date_id_df.columns = self.query_word

        # date_list = agg_df.index.astype(str).tolist()
        date_list = [i.strftime("%Y/%m/%d %H:%M:%S") for i in agg_df.index.to_list()]
        fig = (
            Line()
            .add_xaxis(date_list)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="情感趨勢"),
                xaxis_opts=opts.AxisOpts(type_="time", min_="dataMin", max_="dataMax"),
                yaxis_opts=opts.AxisOpts(type_="value", min_="dataMin", max_="dataMax"),
                # datazoom_opts=opts.DataZoomOpts(type_="inside"),
                brush_opts=opts.BrushOpts(
                    # tool_box=["rect", "lineX", "lineY", "clear"],
                    tool_box=["lineX", "clear"],
                    brush_type="lineX",
                    brush_mode="single",
                    # y_axis_index="all",
                    x_axis_index=0,
                    # series_index="all",
                    throttle_type="debounce",
                    throttle_delay=300,
                ),
            )
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        )
        for col in agg_df.columns:
            fig.add_yaxis(col, agg_df[col].tolist(), is_smooth=True)

        return fig, date_id_df
