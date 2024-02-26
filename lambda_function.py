import boto3  # AWSのサービスを利用するためのライブラリをインポート
import json  # JSON形式のデータを扱うためのライブラリをインポート
import base64  # Base64エンコード・デコードを行うためのライブラリ
import zlib  # データの圧縮・解凍を行うためのライブラリ
import logging  # ログ出力のためのライブラリ
import datetime  # 日付や時間を扱うためのライブラリ
import os  # OSの機能を扱うためのライブラリ（ここでは環境変数を読むために使用）

# AWSのサービスクライアントを初期化（SNSとCloudWatch Logs）
sns = boto3.client('sns')
logs_client = boto3.client('logs')

# ログ設定：情報レベル以上のログを出力
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からログスイッチの設定を読み込み（デフォルトはFalse）
Log_switch = os.getenv('Log_switch', 'False').lower() == 'True'

# 環境変数から設定項目を読み込み
sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
log_group_name = os.getenv('LOG_GROUP_NAME')
log_stream_name = os.getenv('LOG_STREAM_NAME')
keyword = os.getenv('KEYWORD')

# Lambda関数のメイン処理
def lambda_handler(event, context):
    action_log = []  # 処理ログを保持するリスト
    try:
        # トリガー情報の読み込み
        source = context.invoked_function_arn
        time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S %Z')
        action_log.append(f"Triggered at: {time}, Source: {source}")

        # CloudWatch Logsのデータをデコードして解凍
        cw_data = base64.b64decode(event['awslogs']['data'])
        cw_data = zlib.decompress(cw_data, zlib.MAX_WBITS | 32)
        log_events = json.loads(cw_data)['logEvents']

        # ログイベントを処理し、キーワードを検索
        matched_logs = []
        for event in log_events:
            action_log.append(f"Keys in log: {list(event.keys())}")
            if keyword in event['message']:
                matched_logs.append(event)

        # キーワードが含まれるログがあればSNSに通知
        if matched_logs:
            message = '\n'.join([event['message'] for event in matched_logs])
            sns.publish(TopicArn=sns_topic_arn, Message=message, Subject='Log Alert: Matched Keyword')
            action_log.append(f"Matched logs sent via SNS: {message}")
        else:
            action_log.append(f"No logs matched the keyword : {keyword}")

    except Exception as e:
        action_log.append(f"Error processing log event: {str(e)}")
        action_log.append(f"Triggered log data: {event}")

    finally:
        # Log_switchがTrueならCloudWatch Logsに、そうでなければコンソールにログを出力
        final_log = '\n'.join(action_log)
        if Log_switch:
            put_log_events(log_group_name, log_stream_name, final_log)
        else:
            print(final_log)
        print(message)

# CloudWatch Logsにログを出力する関数
def put_log_events(log_group_name, log_stream_name, message):
    try:
        response = logs_client.describe_log_streams(logGroupName=log_group_name, logStreamNamePrefix=log_stream_name)
        if not response['logStreams']:
            logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
        logs_client.put_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            logEvents=[{
                'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                'message': message
            }]
        )
    except logs_client.exceptions.ResourceNotFoundException:
        logs_client.create_log_group(logGroupName=log_group_name)
        logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
        put_log_events(log_group_name, log_stream_name, message)
    except Exception as e:
        print(f"Failed to put log events: {str(e)}")



'''
###test＿demolog
{
  "awslogs": {
    "data":"H4sIAKfb1WUC/1WR3U6EMBCFX4X0WqGw/1xJlMVNdDWBvdFsSGUn2ARoUwq62ey726GgMenF9JyP6ZzhQmpoW1ZCdpZAQoc8RFmUP8dpGiUxuXGI+GpAoeEHs/liuVpvqB+gUYkyUaKT6ME3q2UFT5Nk7VQrYPV/f9QM0HYfbaG41Fw0W15pUK1B3yfWSuRoW8U9NHrwL+ROczOzNhS2DmgQ3FLfnIzScDgupfQNnygEdtKQa1Yi+3jYJ4dXdMbQKN6PkBMlOyd0/pjWMGa26oTUeMl/t2D7N6ONFRQYJd+sV8vFfBb4SEDTcyWa2kyPmFTi1A3YsCLooUJ5t9++oCCZ/sS71zPlmdRefc6ZlK4p7UCqt//CViazO27LNVEnhBdDLvttPinX4/UHCNIn4ewBAAA="}
}
'''