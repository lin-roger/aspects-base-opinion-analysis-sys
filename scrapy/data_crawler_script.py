from elasticsearch import Elasticsearch, helpers
from dcard_crawler import DcardCrawler
from icecream import ic
from tqdm import tqdm
import datetime
import json
import pickle
import pandas as pd
import sys 
    

ic("Elasticsearch client connecting...")
# client = Elasticsearch(
#     "https://elasticsearch:9200",
#     api_key="YjVwMHpKSUI1aVdrRE5nRHhQN0o6UkxLTGRoUGRSVDZic3NCU2IzNFVnQQ==",
#     verify_certs=False,
# )
client = Elasticsearch("http://elasticsearch:9200", verify_certs=False, basic_auth=("elastic", "123456"))


ic("DcardCrawler object creating...")
crawler = DcardCrawler()

settin_body = {
    "index": {
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
        }
    }
}

mapping_body = {
    "properties": {
        "status_code": {"type": "keyword"},
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

idx_name = "dcard"
fname_prifix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

ic("Index creating...")
if not client.indices.exists(index=idx_name):
    client.indices.create(
        index=idx_name, mappings=mapping_body, settings=settin_body, timeout="-1"
    )

ic("Article list getting...")

with open("bords.json") as f:
    boards = json.load(f)
article_list = crawler.get_article_info_list_from_board(
    board=boards, least_n_days=int(sys.argv[1])
)
# article_list = crawler.get_article_info_list_from_board(
#     least_n_days=1
# )[:1]
article_list_T = list(zip(*article_list))
with open(f"./tmp/{fname_prifix}_article_list_T.pkl", 'wb') as f:
    pickle.dump(article_list_T, f)

ic("Article content and comment getting...")
context_list = [
    crawler.get_article_content_and_comment_by_url(i) for i in tqdm(article_list_T[1])
]
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
            "_op_type": "create",
            "_index": idx_name,
            "_id": i["id"],
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

    ic("Data inserting...")
    helpers.bulk(client, data_generater)
except Exception as e:
    print(e)
    ic("Data inserting failed...")
    df.to_pickle(f"./tmp/{fname_prifix}_df.pkl")
