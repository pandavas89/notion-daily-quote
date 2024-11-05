'''
app that inserts designated api based on notion api
'''
import datetime
from zoneinfo import ZoneInfo


from dynamodb import DynamoDB
from s3 import S3
from notion import Notion

def main():
    dynamodb = DynamoDB()
    s3 = S3()
    notion = Notion()

    # 명언 데이터베이스 정보 취득
    quote_datas = dynamodb.read_datas()
    utc_now = datetime.datetime.now(ZoneInfo("UTC"))
    print(f"Now is {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    today = utc_now.astimezone(ZoneInfo("Asia/Seoul")).date()
    print(f"Today is {today}")

    # 명언 데이터베이스별 처리
    for quote in quote_datas:
        status, df = s3.read_quote(quote['bucket'], quote['file'])
        quote_modular = df.shape[0]
        subscriptions = dynamodb.read_subscription(quote['quote_id'], quote_modular, today)
        for mod, sub_list in subscriptions.items():
            # 오늘의 인용구 추출
            today_quote = df[mod + 1]
            # 개별 구독에 대해 처리
            for database_id in sub_list:
                try:
                    notion.daily_customization(database_id)
                except:
                    print("daily customization not found")
                page_found, block_id = notion.find_today_page(database_id)
                # 당일 문서가 발견된 경우
                if page_found:
                    notion.replace_quote(block_id, today_quote[1])
                    notion.insert_quote(block_id, today_quote[0])
                else:
                    print('block not found')


if __name__ == "__main__":
    main()
        