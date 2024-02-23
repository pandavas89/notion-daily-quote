from dotenv import load_dotenv
from pprint import pprint
import os
import datetime

from notion_client import Client
from notion_client.helpers import iterate_paginated_api as paginate

client = Client(auth=os.getenv('NOTION_API'))

def find_today_page(database_id: str) -> tuple:
    '''
    [QUOTE] 구문이 존재하는 오늘 날짜의 페이지를 찾고, 존재한다면 True를 리턴한다
    '''
    page_list = []
    target_id = ''
    for idx, page in enumerate(paginate(client.databases.query, database_id=database_id, page_size=1)):
        if idx > 2:
            break
        page_list.append(page)
    
    for page in page_list:
        page_date = page['properties']['Created']['created_time'][:-5]
        page_date = datetime.datetime.strptime(page_date, '%Y-%m-%dT%H:%M:%S')
        if page_date.date() == datetime.datetime.today().date():
            #print(''.join([x['plain_text'] for x in page['properties']['Name']['title']]))
            target_id = page['id']
            block_found, block_id = search_block(page['id'])
            if block_found:
                return block_found, block_id
    print("Today's block with database_id is not found on {database_id}")
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

def read_block(block_id: str) -> str:
    '''
    read block content
    '''
    result = client.blocks.retrieve(block_id)
    return ''.join([x['plain_text'] for x in result['paragraph']['rich_text']])[7:]

def replace_quote(block_id: str, text: str):
    '''
    replace target block with quote
    '''
    result = client.blocks.update(
        block_id,
        paragraph={"rich_text": [{"type": "text", "text": {"content": text}}]}
    )
    return result

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
