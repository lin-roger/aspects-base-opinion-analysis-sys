# import time
# from urllib import request
from collections import defaultdict
from dateutil.parser import parse
from elasticsearch import Elasticsearch, helpers
from dcard_crawler import DcardCrawler
from ptt_crawler import get_ptt_article_generator

# from utility import inference_check, pipeline_check, index_check
from variables import mapping_body, settin_body
from apscheduler.schedulers.blocking import BlockingScheduler
from tqdm import tqdm

import time
import json
import pandas as pd
import logging
import yaml


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s:%(message)s",
    filename="data_crawler_script.log",
    filemode="a",
)


def inference_check(client: Elasticsearch):
    try:
        client.inference.get(inference_id="tencentbac_conan_embedding_v1")
    except Exception as e:
        print("Inference creating...")
        logging.info("Inference creating...")
        client.inference.put(
            task_type="text_embedding",
            inference_id="tencentbac_conan_embedding_v1",
            body={
                "service": "openai",
                "service_settings": {
                    "model_id": "tencentbac_conan_embedding_v1",
                    "url": "http://localai:8080/embeddings",
                    "api_key": "ignored",
                },
            },
        )


def pipeline_check(client: Elasticsearch):
    try:
        client.ingest.get_pipeline(id="tencentbac_conan_embedding_pipe")
    except Exception as e:
        print("Pipeline creating...")
        logging.info("Pipeline creating...")
        client.ingest.put_pipeline(
            id="tencentbac_conan_embedding_pipe",
            body={
                "processors": [
                    {
                        "inference": {
                            "model_id": "tencentbac_conan_embedding_v1",
                            "input_output": [
                                {
                                    "input_field": "title",
                                    "output_field": "title_vector",
                                },
                                {
                                    "input_field": "context",
                                    "output_field": "context_vector",
                                },
                            ],
                            "if": "ctx?.context_vector? == null",
                        }
                    }
                ]
            },
        )


def index_check(client: Elasticsearch, idx_name: str):
    if not client.indices.exists(index=idx_name):
        print("Index creating...")
        logging.info("Index creating...")
        client.indices.create(
            index=idx_name, mappings=mapping_body, settings=settin_body, timeout="-1"
        )


def ptt_crawler_job():
    for board in platforms["ptt"]["boards"]:
        print(f"`{board}` Article list getting...")
        logging.info(f"`{board}` Article list getting...")
        data_generater = get_ptt_article_generator(
            idx_name=idx_name, board=board, least_n_days=least_n_days
        )
        for ok, result in helpers.streaming_bulk(
            client=client,
            actions=data_generater,
            chunk_size=50,
            request_timeout=60 * 3,  # 3 minutes
            yield_ok=False,
        ):
            if ok is not True:
                logging.error("Failed to import data")
                logging.error(str(result))

        # try:
        #     print("Data inserting...")
        #     helpers.bulk(client, data_generater, request_timeout)
        # except Exception as e:
        #     logging.exception(e)
        #     print("Data inserting failed...")


def dcard_crawler_job():
    for board in platforms["dcard"]["boards"]:
        print(f"`{board}` Article list getting...")
        logging.info(f"`{board}` Article list getting...")
        article_list = crawler.get_article_info_list_from_board(
            board=board, least_n_days=least_n_days
        )
        article_list_T = list(zip(*article_list))

        print(f"`{board}` Article content and comment getting...")
        logging.info(f"`{board}` Article content and comment getting...")
        context_list = [
            crawler.get_article_content_and_comment_by_url(i)
            for i in tqdm(article_list_T[1])
        ]

        context_list_T = list(zip(*context_list))

        df = pd.DataFrame(
            {
                "id": article_list_T[0],
                "link": article_list_T[1],
                "title": article_list_T[2],
                "date": article_list_T[3],
                "context": context_list_T[0],
                "comments": context_list_T[1],
                "crawl_time": context_list_T[2],
            }
        )

        tmp = df.to_json(date_format="iso", orient="records")
        data = json.loads(tmp)

        data_generater = (
            {
                "_op_type": "index",
                "_index": idx_name,
                "platform": "Dcard",
                "borad": board,
                "status_code": "UN_ASTE",
                "link": i["link"],
                "title": i["title"],
                "date": i["date"].replace("T", " ").replace("Z", ""),
                "crawl_time": i["crawl_time"].replace("T", " ").replace("Z", ""),
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

        for ok, result in helpers.streaming_bulk(
            client=client,
            actions=data_generater,
            chunk_size=50,
            request_timeout=60 * 3,  # 3 minutes
            yield_ok=False,
        ):
            if ok is not True:
                logging.error("Failed to import data")
                logging.error(str(result))
        # try:
        #     print("Data inserting...")
        #     helpers.bulk(client, data_generater)
        # except Exception as e:
        #     logging.exception(e)
        #     print("Data inserting failed...")
        
def remove_duplicate_data():
    print("Removing duplicate data...")
    logging.info("Removing duplicate data...")
    body = {
        "_source": False,
        "query": {
            "match_all": {},
        },
        "fields": ["link", "crawl_time"],
    }
    res = list(helpers.scan(client, query=body, index=idx_name))
    dd = defaultdict(list)
    for i in res:
        dd[i["fields"]["link"][0]].append((i["_id"], parse(i["fields"]["crawl_time"][0])))
    del_ids_list = []
    for k, v in dd.items():
        if len(v) > 1:
            tmp = list(zip(*v))
            argmax = tmp[1].index(max(tmp[1]))
            del_ids = list(tmp[0])
            del_ids.pop(argmax)
            del_ids_list.extend(del_ids)
    def gen_del_body(del_ids_list):
        for i in del_ids_list:
            yield {
                "_op_type": "delete",
                "_index": idx_name,
                "_id": i,
            }
    
    print(f"Duplicate data {str(len(del_ids_list))} removed...")
    logging.info(f"Duplicate data {str(len(del_ids_list))} removed...")
    helpers.bulk(client, gen_del_body(del_ids_list))


time.sleep(60)

# load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)
idx_name = config["index"]
platforms = config["platforms"]
least_n_days = config["least_n_days"]
sche = config["scheduler"]


# load mapping and setting
print("Elasticsearch client connecting...")
logging.info("Elasticsearch client connecting...")
client = Elasticsearch(
    "http://elasticsearch:9200", verify_certs=False, basic_auth=("elastic", "123456")
)

inference_check(client)
pipeline_check(client)
index_check(client, idx_name)


# create DcardCrawler object
print("DcardCrawler object creating...")
logging.info("DcardCrawler object creating...")
crawler = DcardCrawler()

if sche:
    scheduler = BlockingScheduler()
    scheduler.add_job(dcard_crawler_job, "cron", hour="4,10,16,22")
    scheduler.add_job(ptt_crawler_job, "cron", hour="4,10,16,22")
    scheduler.add_job(remove_duplicate_data, "cron", hour="4,10,16,22")
    scheduler.start()
else:
    dcard_crawler_job()
    ptt_crawler_job()
    remove_duplicate_data()
