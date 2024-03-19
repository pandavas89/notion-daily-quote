from dotenv import load_dotenv
from pprint import pprint
import os
import datetime
from pprint import pprint

from notion_client import Client
from notion_client.helpers import iterate_paginated_api as paginate


class Notion():
    client = Client(auth=os.getenv('NOTION_API'))
    tz = datetime.tzinfo()
    

    def daily_customization(self, database_id: str):
        '''
        일간 세팅 정리
        '''

        # 타겟 일자 timezone 부여
        today = datetime.datetime.now()
        today = today.replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=9)))

        for page in self.get_pages(database_id, 3):
            
            # 페이지 작성 일자 추출
            page_date = page['properties']['Created']['created_time'][:-5]
            page_date = datetime.datetime.strptime(page_date, '%Y-%m-%dT%H:%M:%S')
            # 페이지 작성 일자 timezone 부여
            page_date = page_date.replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=9)))
            
            # 당일 작성 페이지에 해당하는 경우
            if page_date.date() == today.date():
                # 제목 추출
                title = ''.join([x['plain_text'] for x in page['properties']['Name']['title']])
                new_title = ''
                # 일성록 및 주간 리뷰 개별 처리
                if title == '일성록':
                    new_title = page_date.strftime(f'%y%m%d {title}')
                # 일요일이 ISO WEEKDAY 7이므로 +1 해줘야 일-월 가능
                elif title == '주간 리뷰':
                    new_title = (page_date + datetime.timedelta(days=1)).strftime(f'%Y-%W {title}')
                    
                # 일자 연결이 필요한 제목인 경우에 한정하여 반영
                if new_title:
                    update_dict = {
                        'Name': {'title': [{'text': {'content': new_title}}]},
                        '일자': {'date': {'start': today.strftime('%Y-%m-%d')}}
                    }
                    self.client.pages.update(today, properties=update_dict)

    def get_pages(self, database_id: str, page_count: int) -> list:
        '''
        get page of given page count
        '''
        page_list = []
        for idx, page in enumerate(paginate(self.client.databases.query, database_id=database_id)):
            if len(page_list) == page_count:
                break
            page_list.append(page)
        return page_list


    def find_today_page(self, database_id: str) -> tuple:
        '''
        [QUOTE] 구문이 존재하는 오늘 날짜의 페이지를 찾고, 존재한다면 True를 리턴한다
        '''
        target_id = ''
        
        page_list = self.get_pages(database_id, 2)
        
        # 오늘 날짜를 KST(UTC+9)로 전환: notion과 github action 모두 UTC를 제공함
        today = datetime.datetime.now()
        today.replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone.dst(9))
        
        # 페이지별로 검사
        for page in page_list:
            page_date = page['properties']['Created']['created_time'][:-5]

            # 페이지 작성 일자 추출
            page_date = datetime.datetime.strptime(page_date, '%Y-%m-%dT%H:%M:%S')
            page_date.replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone.dst(9))
            
            # 당일 작성 페이지인 경우
            if page_date.date() == today.date():
                
                target_id = page['id']
                block_found, block_id = self.search_block(page['id'])
                if block_found:
                    return block_found, block_id
        print(f"Today's block with database_id is not found on {database_id}")
        return False, target_id
    
    def find_target_date_page(self, database_id: str, target_date: datetime.date) -> tuple:
        page_list = []
        target_id = ''
        for idx, page in enumerate(paginate(self.client.databases.query, database_id=database_id)):
            if idx > 5:
                break
            page_list.append(page)
        
        for page in page_list:
            page_date = page['properties']['Created']['created_time'][:-5]
            page_date = datetime.datetime.strptime(page_date, '%Y-%m-%dT%H:%M:%S')
            
            if page_date.date() == target_date:
                target_id = page['id']
                
                title = ''.join([x['plain_text'] for x in page['properties']['Name']['title']])
                new_title = ''
                if title == '일성록':
                    new_title = page_date.strftime(f'%y%m%d {title}')
                elif title == '주간 리뷰':
                    new_title = (page_date + datetime.timedelta(days=1)).strftime(f'%Y-%W {title}')
                if new_title:
                    print(new_title)
                    update_dict = {
                        'Name': {'title': [{'text': {'content': new_title}}]},
                        '일자': {'date': {'start': target_date.strftime('%Y-%m-%d')}}
                    }
                    self.client.pages.update(target_id, properties=update_dict)
        print(f"Target date's block with database_id is not found on {database_id}")
        return False, target_id
    
    def search_block(self, page_id: str) -> tuple:
        '''
        [QUOTE] 구문이 존재하는 블럭을 찾고, 존재한다면 True, {block_id}를 리턴한다. 존재하지 않는다면 False, ''을 리턴한다.
        '''
        for block in paginate(self.client.blocks.children.list, block_id=page_id):
            if block['has_children']:
                result = self.search_block(block['id'])
                if result[0]:
                    return result
            elif block['type'] == 'paragraph':
                target = (''.join([x['plain_text'] for x in block['paragraph']['rich_text']]))[:7]
                if target == '[QUOTE]':
                    return True, block['id']
        return False, ''
    
    def read_block(self, block_id: str) -> str:
        '''
        read block content
        '''
        result = self.client.blocks.retrieve(block_id)
        return ''.join([x['plain_text'] for x in result['paragraph']['rich_text']])[7:]
    
    def replace_quote(self, block_id: str, text: str):
        '''
        replace target block with quote
        '''
        result = self.client.blocks.update(
            block_id,
            paragraph={"rich_text": [{"type": "text", "text": {"content": text}}]}
        )
        return result
    
    def insert_quote(self, page_id: str, text: str):
        '''
        insert block into target notion page, title in 1-depth deeper
        '''
        result = self.client.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "type": "paragraph", 
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
                }
            ])
        return result
    
    def change_title(self, page_id: str):
        '''
        change title to format of YYMMDD 일성록
        '''
        
        
    
    def set_date(self, date: str):
        '''
        update date
        '''
