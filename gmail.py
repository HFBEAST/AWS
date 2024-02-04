import boto3
import json
import base64
import zlib
import email.utils
from botocore.exceptions import ClientError

# 初始化 SES 客户端
ses_client = boto3.client('ses')

def lambda_handler(event, context):
    try:
        # 对 CloudWatch Logs 数据进行解码和解压缩
        cw_data = base64.b64decode(event['awslogs']['data'])
        cw_logs = json.loads(zlib.decompress(cw_data, 16+zlib.MAX_WBITS))

        # 解析日志事件消息
        for log_event in cw_logs['logEvents']:
            # message = json.loads(log_event['message'])
            full_log_message = json.dumps(log_event, indent=4)
            
            # 构建邮件正文，包括日志组信息、日志流信息以及日志内容
            email_body = (
                f"Log Group: {cw_logs['logGroup']}\n"
                f"Log Stream: {cw_logs['logStream']}\n"
                # f"Log Message: {message['message']}\n"
                f"Log Event: {full_log_message}\n"
            )
            
            # 发送邮件
            response = ses_client.send_email(
                Source='yyp820674026@gmail.com',  # 更换为您的验证邮箱
                Destination={
                    'ToAddresses': [
                        'yyp820674026@gmail.com',  # 更换为目的 Gmail 地址
                    ]
                },
                Message={
                    'Subject': {
                        'Data': 'Log Update Notification',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': email_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            print(response)
    except Exception as e:
        print(e)
        raise e
