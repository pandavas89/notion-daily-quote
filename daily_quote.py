'''
app that inserts designated api based on notion api
'''
import datetime


from dynamodb import DynamoDB
from s3 import S3
from notion import Notion


dynamodb = DynamoDB()
s3 = S3()
notion = Notion()

# 명언 데이터베이스 정보 취득
quote_datas = dynamodb.read_datas()
today = datetime.datetime.today()
print(f"Today is {today.strftime('%Y-%m-%d %H:%M:%S')}")
today = today.date()

# 명언 데이터베이스별 처리
for quote in quote_datas:
    status, df = s3.read_quote(quote['bucket'], quote['file'])
    quote_modular = df.shape[0]
    subscriptions = dynamodb.read_subscription(quote['quote_id'], quote_modular, today)
    for mod, sub_list in subscriptions.items():
        # 오늘의 인용구 추출
        today_quote = df.iloc[mod, :]
        # 개별 구독에 대해 처리
        for database_id in sub_list:
            page_found, block_id = notion.find_today_page(database_id)
            # 당일 문서가 발견된 경우
            if page_found:
                notion.replace_quote(block_id, today_quote['Quote'])
                notion.insert_quote(block_id, today_quote['Verse'])
            else:
                print('block not found')
        