import boto3
import urllib.parse
import datetime
from pytz import timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('notion-daily-quote-subscription')

def lambda_handler(event, context):
    body = urllib.parse.parse_qs(event['body'])
    
    today = datetime.datetime.now().replace(tzinfo=timezone('Asia/Seoul')).date()
    item = {
        'quote_id': int(body['quote_id']),
        'start_date': (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        'database_id': body['database_id']
    }
    
    response = table.put_item(Item=item)
    
    return {
        'statusCode': 200,
        'body': '데이터가 성공적으로 업데이트되었습니다'
    }