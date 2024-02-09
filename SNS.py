import boto3
import json
import base64
import zlib

# SNSクライアントの初期化
sns = boto3.client('sns')

# SNSコンソールで見つけた正確なトピックARNに置き換えます
sns_topic_arn = 'arn:aws:sns:ap-northeast-1:441133636880:scissionID'

def lambda_handler(event, context):
    # CloudWatch Logsデータのデコードと解凍
    cw_data = base64.b64decode(event['awslogs']['data'])
    cw_data = zlib.decompress(cw_data, zlib.MAX_WBITS | 32)
    log_events = json.loads(cw_data)['logEvents']

    # ログメッセージの抽出
    log_messages = [event['message'] for event in log_events]

    # 通知メッセージの内容の構築
    message = '\n'.join(log_messages)

    # SNSトピックにメッセージを送信
    sns_response = sns.publish(
        TopicArn=sns_topic_arn,
        Message=message,
        Subject='Log Alert'
    )
    print("######message :", message)
    return sns_response
