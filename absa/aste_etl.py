from http import client
from icecream import ic, install

install()
ic.disable()

# %%
import logging

FORMAT = "%(asctime)s %(filename)s %(levelname)s:%(message)s"
logging.basicConfig(
    level=logging.ERROR, format=FORMAT, filename="etl.log", filemode="a"
)


# %%
from elasticsearch import Elasticsearch, helpers
import eland as ed

from spacy import displacy
from spacy import blank
from spacy import load
from MyUtilty.tag2pos import tag2posFactory
from MyUtilty.psoPipe import PendingAspectsOpinionsPipe
from MyUtilty.cost_seg import CostSegmenter
from MyUtilty.emoBankSearch import EmoBankSearch
from spacy.tokens import Doc

import functools
import time
from json import loads
from typing import TypedDict


class AOP_dict(TypedDict):
    a: str
    o: str
    p: float


Doc.set_extension("pending_aspects_opinions_i", default=[])
Doc.set_extension("pending_aspects_opinions_text", default=[])
Doc.set_extension("aspect_sentiment_triplets", default=[])

nlp = blank("xx")
nlp.tokenizer = CostSegmenter(nlp.vocab)
nlp.add_pipe("tag2pos")
nlp.add_pipe("pending_aspects_opinions_pipe")

nlp_latin = load("./vec")
EBS = EmoBankSearch(nlp_latin)
EBS_Dict = functools.partial(EBS, to_dict=True)

# client = Elasticsearch(
#     "https://elasticsearch:9200",
#     api_key="YjVwMHpKSUI1aVdrRE5nRHhQN0o6UkxLTGRoUGRSVDZic3NCU2IzNFVnQQ==",
#     verify_certs=False,
# )
client = Elasticsearch("http://elasticsearch:9200", verify_certs=False, basic_auth=("elastic", "123456"))


# %%
def infer(text: str) -> list[AOP_dict]:
    doc = EBS_Dict(nlp(text))
    return doc._.aspect_sentiment_triplets

def aste_infer(texts: list[str]) -> list[list[AOP_dict]]:
    return [infer(text) if text else None for text in texts]


def comments_aste_infer(comments: list[dict]) -> list[dict]:
    comments = [
        {
            "content": comment["content"],
            "content_aste": infer(comment["content"])
        }
        for comment in comments
        if comment["content"]
    ]
    return comments


# %%
backoff_count = 1
while True:
    ed_data = (
        ed.DataFrame(
            client,
            "dcard",
            columns=[
                "status_code",
                "link",
                "title",
                "title_aste",
                "date",
                "context",
                "context_aste",
                "comments",
            ],
        )
        .query("status_code == 'UN_ASTE'")
        .head(5)
    )
    if not ed_data.empty:
        backoff_count = 1
        print("Processing data")
        try:
            pd_data = ed.eland_to_pandas(ed_data)
            pd_data["status_code"] = "HAS_ASTE"
            pd_data["title_aste"] = aste_infer(pd_data["title"].values)
            pd_data["context_aste"] = aste_infer(pd_data["context"].values)
            pd_data["comments"] = pd_data["comments"].apply(comments_aste_infer)
        except Exception as e:
            print("Error in processing data")
            logging.error("Error in processing data")
            logging.exception(e)
            logging.error("ID: %s", str(list(pd_data.index)))
            break

        print("Updating data")

        # buf = pd_data.to_json(date_format="iso")
        # parsed = loads(buf)
        # print(parsed)
        # break

        try:
            # ed.pandas_to_eland(pd_data, client, "dcard", es_if_exists="append", es_type_overrides={'comments':'nested', 'title_aste':'nested', 'context_aste':'nested'})
            for idx, data in pd_data.iterrows():
                client.update(
                    index="dcard",
                    id=idx,
                    body={
                        "doc": {
                            "status_code": data["status_code"],
                            "title_aste": data["title_aste"],
                            "context_aste": data["context_aste"],
                            "comments": data["comments"],
                        },
                    },
                )
        except Exception as e:
            print("Error in updating data")
            logging.error("Error in updating data")
            logging.exception(e)
            break

        print("Data processed")

    else:
        logging.info("No data to process")
        time.sleep(5**backoff_count)
        if backoff_count < 4:
            backoff_count += 1
