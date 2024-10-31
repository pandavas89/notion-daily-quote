from daily_quote import main

def lambda_handler(event, context):
    main()

    return {
        'statusCode': 200,
        'body': '람다 함수가 성공적으로 실행되었습니다'
    }