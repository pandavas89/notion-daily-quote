'''
app that inserts designated api based on notion api
'''
from dotenv import load_dotenv

import datetime
from pprint import pprint
import os
import pandas as pd

from notion_client import Client
from notion_client.helpers import iterate_paginated_api as paginate

load_dotenv()
database_id = 'b3ae83876f3f43bcb6eedff250f0a73f'
START_DATE = datetime.date(2024, 1, 1)
client = Client(auth=os.getenv('NOTION_API'))

date_name = '일자'

def find_today_page(database_id: str) -> tuple:
    '''
    오늘 날짜의 페이지를 찾고, 존재한다면 True를 리턴한다
    '''
    page_list = []
    target_id = ''
    for idx, page in enumerate(paginate(client.databases.query, database_id=database_id, page_size=1)):
        if idx > 2:
            break
        page_list.append(page)
    
    for page in page_list:
        page_date = page['properties'][date_name]['date']['start']
        page_date = datetime.datetime.strptime(page_date, '%Y-%m-%d')
        if page_date.date() == datetime.datetime.today().date():
            #print(''.join([x['plain_text'] for x in page['properties']['Name']['title']]))
            target_id = page['id']
            return True, target_id
    return False, target_id

def search_block(page_id: str) -> tuple:
    '''
    recursively search throguh page for given starting block - [QUOTE]
    '''
    for block in paginate(client.blocks.children.list, block_id=page_id):
        if block['has_children']:
            result = search_block(block['id'])
            if result[0]:
                return result
        elif block['type'] == 'paragraph':
            target = (''.join([x['plain_text'] for x in block['paragraph']['rich_text']]))[:7]
            if target == '[QUOTE]':
                return True, block['id']
    return False, ''

def replace_block(block_id: str, text: str):
    '''
    replace target block with quote
    '''
    result = client.blocks.update(
        block_id,
        paragraph={"rich_text": [{"type": "text", "text": {"content": text}}]}
    )
    return result

def load_data(start_date: str) -> tuple:
    '''
    데이터를 불러온다
    '''
    raw_data = pd.read_excel('dharma sutra_kr.xlsx')
    today_idx = (datetime.date.today() - datetime.datetime.strptime(start_date, '%Y-%M-%d').date()).days
    target_quote = raw_data.iloc[today_idx, 0:3]
    return target_quote['Verse'], target_quote['Quote']

def insert_quote(page_id: str, text: str):
    '''
    insert block into target notion page, title in 1-depth deeper
    '''
    result = client.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "type": "paragraph", 
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
            }
        ])
    return result

def read_block(block_id: str) -> str:
    '''
    read block content
    '''
    result = client.blocks.retrieve(block_id)
    return ''.join([x['plain_text'] for x in result['paragraph']['rich_text']])[7:]

page_found, page_id = find_today_page(database_id)

# acutal flow
# target block: QUOTE로 시작하는 블록을 찾는다
quote_found, quote_id = search_block(page_id)
print(quote_found, quote_id)

# block의 내용을 읽어온다
quote_data = read_block(quote_id)

# quote option을 확인한다
start_date, quote_origin = quote_data.split(':')

# quote option에 따른 데이터를 가져온다
header, text = load_data(start_date)

# text로 block을 치환한다
replace_block(quote_id, text)
insert_quote(quote_id, header)