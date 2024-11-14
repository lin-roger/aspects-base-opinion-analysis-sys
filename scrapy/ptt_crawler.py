from math import e
from bs4 import BeautifulSoup
from PttWebCrawler.crawler import PttWebCrawler
from datetime import datetime, timedelta
from dateutil import parser

import os, sys
import requests
import re
import time
import json

VERIFY = True
PTT_URL = "https://www.ptt.cc"

class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def _parse_articles(index, board, timeout=3):
    link_aid_board_set = set()
    resp = requests.get(
        url=PTT_URL + "/bbs/" + board + "/index" + str(index) + ".html",
        cookies={"over18": "1"},
        verify=VERIFY,
        timeout=timeout,
    )
    if resp.status_code != 200:
        print("invalid url:", resp.url)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    divs = soup.find_all("div", "r-ent")
    for div in divs:
        try:
            # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
            href = div.find("a")["href"]
            link = PTT_URL + href
            article_id = re.sub("\.html", "", href.split("/")[-1])
            link_aid_board_set.add((link, article_id, board))
        except:
            pass
    return list(link_aid_board_set)


def _gen_es_article(article, idx_name, board, link):
    def comment_ipdatetime_2_datetime(ipdatetime: str, year: str) -> datetime:
        ipdatetime = ipdatetime.split(" ")
        if len(ipdatetime) == 3:
            dt = parser.parse(f"{year}/{ipdatetime[1]} {ipdatetime[2]}", ignoretz=True)
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        if len(ipdatetime) == 2:
            dt = parser.parse(f"{year}/{ipdatetime[0]} {ipdatetime[1]}", ignoretz=True)
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return None

    date = article["date"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    crawl_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    es_article = {
        "_op_type": "index",
        "_index": idx_name,
        "status_code": "UN_ASTE",
        "platform": "PTT",
        "borad": board,
        "link": link,
        "date": date,
        "crawl_time": crawl_time,
        "title": article["article_title"],
        "context": article["content"],
        "comments": [
            {
                "username": message["push_userid"],
                "content": message["push_content"],
                "date": comment_ipdatetime_2_datetime(
                    message["push_ipdatetime"], date[:4]
                ),
            }
            for message in article["messages"]
            if message["push_content"]
        ],
    }
    return es_article


def get_ptt_article_generator(
    idx_name: str, board="Gossiping", least_n_days: float = 7
):
    least_n_days = timedelta(days=least_n_days)
    last_page = PttWebCrawler.getLastPage(board)
    page_pointer = last_page
    now = datetime.now()
    while page_pointer > 0:
        link_aid_board_list = _parse_articles(page_pointer, board)
        print(page_pointer)
        for link, aid, board in link_aid_board_list:
            time.sleep(0.1)
            try:
                with HiddenPrints():
                    article_str = PttWebCrawler.parse(link, aid, board)
                    
                article = json.loads(article_str)
                article["date"] = parser.parse(
                    article["date"], ignoretz=True
                ) - timedelta(hours=8)
                print(article["date"])
            
                if (now - article["date"]) > least_n_days:
                    if page_pointer == last_page:
                        continue
                    else:
                        print(page_pointer, link, aid, board)
                        page_pointer = 0
                        break
                else:
                    yield _gen_es_article(article, idx_name, board, link)

            except Exception as e:
                continue
        page_pointer -= 1
