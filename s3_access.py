import io
import os
import boto3
import pandas as pd

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

response = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key='dharma sutra_kr.xlsx')
status = response.get('ResponseMetadata', {}).get('HTTPStatusCode')

if status == 200:
    print(f'Successful S3 get_object response. Status - {status}')
    target_df = pd.read_excel(io.BytesIO(response['Body'].read()))
    print(target_df)