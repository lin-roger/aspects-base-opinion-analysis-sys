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
from MyUtilty.mergePipe import MergePipe
from MyUtilty.cost_seg import CostSegmenter
from MyUtilty.emoBankSearch import EmoBankSearch
from spacy.tokens import Doc

import functools
import time
import yaml
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
nlp.add_pipe("merge_pipe")
nlp.add_pipe("pending_aspects_opinions_pipe")

nlp_latin = load("./vec")
EBS = EmoBankSearch(nlp_latin)
EBS_Dict = functools.partial(EBS, to_dict=True)

with open("config.yaml") as f:
    config = yaml.safe_load(f)
idx_name = config["index"]
client = Elasticsearch(
    "http://elasticsearch:9200", verify_certs=False, basic_auth=("elastic", "123456")
)


# %%
# def infer(text: str) -> list[AOP_dict]:
#     doc = EBS_Dict(nlp(text))
#     return doc._.aspect_sentiment_triplets

def text2doc(text: str) -> Doc:
    if text:
        return EBS_Dict(nlp(text))
    else:
        return None

def comments_aste_infer(comments: list[dict]) -> list[dict]:
    comments = [
        {"content": comment["content"], "content_aste": text2doc(comment["content"])._.aspect_sentiment_triplets}
        for comment in comments
        if comment["content"]
    ]
    return comments


def gen_update_body(data):
    for idx, row in data.iterrows():
        yield {
            "_op_type": "update",
            "_index": idx_name,
            "_id": idx,
            "doc": {
                "status_code": row["status_code"],
                "title_aste": row["title_aste"],
                "title_token": row["title_token"],
                "title_tag": row["title_tag"],
                "context_aste": row["context_aste"],
                "context_token": row["context_token"],
                "context_tag": row["context_tag"],
                "comments": row["comments"],
            },
        }


# %%
backoff_count = 1
while True:
    ed_data = (
        ed.DataFrame(
            client,
            idx_name,
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
        .query("status_code != 'ASTE_BY_RULE_v2'")
        .head(1000)
    )
    if not ed_data.empty:
        backoff_count = 1
        print("Processing data")
        try:
            pd_data = ed.eland_to_pandas(ed_data)
            pd_data["status_code"] = "ASTE_BY_RULE_v2"

            title_doc = pd_data["title"].apply(text2doc)
            pd_data["title_aste"] = title_doc.apply(lambda x: x._.aspect_sentiment_triplets if x else None)
            pd_data["title_token"] = title_doc.apply(lambda x: [token.text for token in x] if x else None)
            pd_data["title_tag"] = title_doc.apply(lambda x: [token.tag_ for token in x] if x else None)
            pd_data["title_dep"] = title_doc.apply(lambda x: [token.dep_ for token in x] if x else None)
            pd_data["title_head"] = title_doc.apply(lambda x: [token.head for token in x] if x else None)

            context_doc = pd_data["context"].apply(text2doc)
            pd_data["context_aste"] = context_doc.apply(lambda x: x._.aspect_sentiment_triplets if x else None)
            pd_data["context_token"] = context_doc.apply(lambda x: [token.text for token in x] if x else None)
            pd_data["context_tag"] = context_doc.apply(lambda x: [token.tag_ for token in x] if x else None)
            pd_data["context_dep"] = context_doc.apply(lambda x: [token.dep_ for token in x] if x else None)
            pd_data["context_head"] = context_doc.apply(lambda x: [token.head for token in x] if x else None)

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
            helpers.bulk(client, gen_update_body(pd_data))
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
