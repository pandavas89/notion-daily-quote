'''
app that inserts designated api based on notion api
'''
from dotenv import load_dotenv
from pprint import pprint
import datetime
import os
import pandas as pd

from notion_client import Client
from notion_client.helpers import iterate_paginated_api as paginate

from dynamodb import read_datas, read_subscription
from s3 import read_quote
from notion import find_today_page, search_block, replace_quote, insert_quote


load_dotenv()

# 명언 데이터베이스 정보 취득
quote_datas = read_datas()
today = datetime.datetime.today()
print(f"Today is {today.strftime('%Y-%m-%d %H:%M:%S')}")
today = today.date()

# 명언 데이터베이스별 처리
for quote in quote_datas:
    status, df = read_quote(quote['bucket'], quote['file'])
    quote_modular = df.shape[0]
    subscriptions = read_subscription(quote['quote_id'], quote_modular, today)
    for mod, sub_list in subscriptions.items():
        # 오늘의 인용구 추출
        today_quote = df.iloc[mod, :]
        # 개별 구독에 대해 처리
        for database_id in sub_list:
            page_found, block_id = find_today_page(database_id)
            # 당일 문서가 발견된 경우
            if page_found:
                replace_quote(block_id, today_quote['Quote'])
                insert_quote(block_id, today_quote['Verse'])
            else:
                print('block not found')
        