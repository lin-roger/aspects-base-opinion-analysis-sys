from calendar import c
from multiprocessing import Pool
from elasticsearch import Elasticsearch, helpers
from dcard_crawler import DcardCrawler

# from icecream import ic
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
import datetime
import json
import pickle
import pandas as pd
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s:%(message)s",
    filename="data_crawler_script.log",
    filemode="a",
)


print("Elasticsearch client connecting...")
client = Elasticsearch(
    "http://elasticsearch:9200", verify_certs=False, basic_auth=("elastic", "123456")
)


print("DcardCrawler object creating...")
crawler = DcardCrawler()

settin_body = {
    "index": {
        "default_pipeline": "tencentbac_conan_embedding_pipe",
        "analysis": {
            "analyzer": {
                "ik_smart_plus": {
                    "type": "custom",
                    "tokenizer": "ik_smart",
                    "filter": ["synonym"],
                },
                "ik_max_word_plus": {
                    "type": "custom",
                    "tokenizer": "ik_max_word",
                    "filter": ["synonym"],
                },
            },
            "filter": {
                "synonym": {
                    "type": "synonym",
                    "synonyms_path": "analysis-ik/dict/zh_synonym.txt",
                }
            },
        },
    }
}

mapping_body = {
    "properties": {
        "status_code": {"type": "keyword"},
        "platform": {"type": "keyword"},
        "borad": {"type": "keyword"},
        "link": {"type": "keyword", "index": False},
        "title": {
            "type": "text",
            "analyzer": "ik_max_word_plus",
            "search_analyzer": "ik_smart_plus",
        },
        "title_aste": {
            "type": "nested",
            "properties": {
                "a": {"type": "keyword"},
                "o": {"type": "keyword"},
                "p": {"type": "float"},
            },
        },
        "title_vector": {"type": "dense_vector"},
        "date": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS"},
        "context": {
            "type": "text",
            "analyzer": "ik_max_word_plus",
            "search_analyzer": "ik_smart_plus",
        },
        "context_aste": {
            "type": "nested",
            "properties": {
                "a": {"type": "keyword"},
                "o": {"type": "keyword"},
                "p": {"type": "keyword"},
            },
        },
        "context_vector": {"type": "dense_vector"},
        "comments": {
            "type": "nested",
            "properties": {
                "username": {
                    "type": "text",
                    "analyzer": "ik_max_word_plus",
                    "search_analyzer": "ik_smart_plus",
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word_plus",
                    "search_analyzer": "ik_smart_plus",
                },
                "content_aste": {
                    "type": "nested",
                    "properties": {
                        "a": {"type": "keyword"},
                        "o": {"type": "keyword"},
                        "p": {"type": "float"},
                    },
                },
                "date": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS"},
            },
        },
    }
}

idx_name = "docs"
try:
    client.inference.get(inference_id="tencentbac_conan_embedding_v1")
except Exception as e:
    print("Inference creating...")
    client.inference.put(
        task_type="text_embedding",
        model_name="tencentbac_conan_embedding_v1",
        body={
            "service": "openai",
            "service_settings": {
                "model_id": "tencentbac_conan_embedding_v1",
                "url": "http://localai:8080/embeddings",
                "api_key": "ignored",
            },
        },
    )

try:
    client.ingest.get_pipeline(id="tencentbac_conan_embedding_pipe")
except Exception as e:
    print("Pipeline creating...")
    client.ingest.put_pipeline(
        id="tencentbac_conan_embedding_pipe",
        body={
            "processors": [
                {
                    "inference": {
                        "model_id": "tencentbac_conan_embedding_v1",
                        "input_output": [
                            {"input_field": "title", "output_field": "title_vector"},
                            {
                                "input_field": "context",
                                "output_field": "context_vector",
                            },
                        ],
                    }
                }
            ]
        },
    )

if not client.indices.exists(index=idx_name):
    print("Index creating...")
    client.indices.create(
        index=idx_name, mappings=mapping_body, settings=settin_body, timeout="-1"
    )


with open("bord_list.json") as f:
    boards = json.load(f)

for board in boards:
    fname_prifix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    print(f"`{board}` Article list getting...")
    article_list = crawler.get_article_info_list_from_board(
        board=board, least_n_days=int(sys.argv[1])
    )
    article_list_T = list(zip(*article_list))
    with open(f"./tmp/{fname_prifix}_article_list_T.pkl", "wb") as f:
        pickle.dump(article_list_T, f)

    print(f"`{board}` Article content and comment getting...")
    context_list = [
        crawler.get_article_content_and_comment_by_url(i)
        for i in tqdm(article_list_T[1])
    ]
    # context_list = process_map(crawler.get_article_content_and_comment_by_url, article_list_T[1], max_workers=8)
    # def wapper(url):
    #     return crawler.get_article_content_and_comment_by_url(url)
    # with Pool(8) as p:
    #     context_list = p.map(wapper, article_list_T[1])

    context_list_T = list(zip(*context_list))
    with open(f"./tmp/{fname_prifix}_context_list_T.pkl", "wb") as f:
        pickle.dump(context_list, f)

    df = pd.DataFrame(
        {
            "id": article_list_T[0],
            "link": article_list_T[1],
            "title": article_list_T[2],
            "date": article_list_T[3],
            "context": context_list_T[0],
            "comments": context_list_T[1],
        }
    )

    try:
        tmp = df.to_json(date_format="iso", orient="records")
        data = json.loads(tmp)

        data_generater = (
            {
                "_op_type": "index",
                "_index": idx_name,
                "_id": i["id"],
                "platform": "Dcard",
                "borad": board,
                "status_code": "UN_ASTE",
                "link": i["link"],
                "title": i["title"],
                "date": i["date"].replace("T", " ").replace("Z", ""),
                "context": i["context"],
                "comments": [
                    {
                        "username": j[0],
                        "content": j[1],
                        "date": j[2].replace("T", " ").replace("Z", ""),
                    }
                    for j in i["comments"]
                    if j[1]
                ],
            }
            for i in data
        )

        print("Data inserting...")
        helpers.bulk(client, data_generater)
    except Exception as e:
        logging.exception(e)
        print("Data inserting failed...")
        df.to_pickle(f"./tmp/{fname_prifix}_df.pkl")
