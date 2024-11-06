from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage._pages.chromium_tab import ChromiumTab
from nlp2 import clean_httplink

# from DrissionPage.common import from_selenium
# from selenium import webdriver
from pyvirtualdisplay import Display
from dateutil import parser
import datetime
import time
import logging

logger = logging.getLogger(__name__)


class DcardCrawler:
    def __init__(self, headless: bool = False):
        self.error_set = []

        display = Display(size=(1920, 1080))
        # display = Display(visible=True, size=(1920, 1080))
        display.start()

        browser_path = "/usr/bin/google-chrome"
        options = ChromiumOptions()
        options.set_argument("--remote-debugging-port=9222")
        options.set_argument("--no-sandbox")  # Necessary for Docker
        options.set_argument("--disable-gpu")  # Optional, helps in some cases
        options.set_argument("--disable-dev-shm-usage")  # Optional, helps in some cases
        options.set_paths(browser_path=browser_path)
        options.headless(headless)
        # options.no_imgs(True)

        self._driver = ChromiumPage(addr_or_opts=options)

    def _comment_exraction(self, commentEle):
        try:
            user_name, commen_context, comment_time = (
                commentEle.child().child().child().child().child(2).children()
            )
            user_name = user_name.child().child().text
            comment_time = comment_time.s_ele("tag:time").attr("datetime")
            return (
                user_name,
                commen_context.text,
                self._date_time_UTC_Taipei(comment_time),
            )
        except Exception as e:
            logger.error(f"Error(No comment): {commentEle.text}")
            logger.exception(e)
            return (None, None, None)

    def _by_pass(self, page: ChromiumTab):
        if page.title == "Dcard 需要確認您的連線是安全的":
            cf_bypasser = CloudflareBypasser(page)
            cf_bypasser.click_verification_button()

    def _date_time_UTC_Taipei(self, dt: datetime.datetime | str):
        if isinstance(dt, str):
            dt = parser.parse(dt, ignoretz=True)
        return dt + datetime.timedelta(hours=8)

    def _get_tab_from_url(self, url: str):
        tab = self._driver.new_tab(url)
        self._by_pass(tab)
        return tab

    def get_article_content_and_comment_by_url(
        self,
        article_url: str,
    ):
        assert "dcard" in article_url
        tab = self._get_tab_from_url(article_url)
        try:
            article_content = remove_httplink(tab.s_ele("css:article > div", index=2).text)
        except Exception as e:
            logger.error(f"Error(No article_content): {article_url}")
            logger.exception(e)
            tab.close()
            return "", []

        tab.scroll.to_bottom()
        tab.wait(1)

        try:
            comment_contents = [
                self._comment_exraction(i)
                for i in tab.s_eles("css:section > div > div")
                if i.text != "" and i.text[0:2] != "查看"
            ]
        except Exception as e:
            logger.error(f"Error(No comment_contents): {article_url}")
            logger.exception(e)
            tab.close()
            return article_content, []

        tab.close()
        return article_content, comment_contents

    def get_article_info_list_from_board(
        self,
        board: str | list[str] = "makeup",
        least_n_days: int = 7,
    ):
        if isinstance(board, str):
            board = [board]
        link_dateTime_set = set()
        today = datetime.date.today()

        for b in board:
            tab = self._get_tab_from_url(f"https://www.dcard.tw/f/{b}?tab=latest")
            scroll = tab.scroll
            # tab.set.load_mode.eager()

            flag = 0
            while flag < 5:
                tab.wait(3)
                aList = tab.s_eles("tag=article")
                for a in aList:
                    try:
                        a_dateTime = self._date_time_UTC_Taipei(
                            a.s_ele("tag=time").attr("datetime")
                        )
                        a_text = a.s_ele("tag=h2").text
                        a_href = a.s_ele("css:h2>a").link
                        a_info = (a_href.split("/")[-1], a_href, a_text, a_dateTime)
                        if (today - a_dateTime.date()).days <= least_n_days and a_info not in link_dateTime_set:
                            flag = 0
                            link_dateTime_set.add(a_info)
                        else:
                            flag += 1
                    except Exception as e:
                        self.error_set.append(a)
                        logger.error(a, a.text)
                        logger.exception(e)
                scroll.to_bottom()

            tab.close()
        return list(link_dateTime_set)
