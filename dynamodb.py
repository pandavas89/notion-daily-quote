from dotenv import load_dotenv

import datetime
import os

import boto3
from boto3.dynamodb.conditions import Key

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

dynamodb = boto3.resource(
    'dynamodb',
    region_name='ap-northeast-2',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

data_table = dynamodb.Table('notion-daily-quote-data')
subscription = dynamodb.Table('notion-daily-quote-subscription')

def read_datas():
    # quote data 정보
    response = data_table.scan()
    return response['Items']

def read_subscription(quote_id: int, mod: int, today: datetime.date):
    # subscription 정보
    subscriptions = {}
    response = subscription.query(KeyConditionExpression = Key('quote_id').eq(quote_id))
    items = response['Items']
    for item in items:
        date = datetime.datetime.strptime(item['start_date'], '%Y-%m-%d').date()
        moded = (today - date).days % mod
        #print(f'{(today - date).days} % {mod} = {moded}')
        if moded in subscriptions:
            subscriptions[moded].append(item['database_id'])
        else:
            subscriptions[moded] = [item['database_id']]
    return subscriptions