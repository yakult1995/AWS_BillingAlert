#!/usr/bin/env python3

import boto3
import datetime
import requests
import json
import os
import os.path
import dotenv

# 環境変数読み込み
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)

# Slack設定
SLACK_URL = os.environ.get("SLACK_URL")
SLACK_ROOM = os.environ.get("SLACK_ROOM")

# 取得する日時の設定
now = datetime.datetime.utcnow()
start = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
end = now.strftime('%Y-%m-%d')

# boto3の呼び出し
cd = boto3.client('ce', 'us-east-1')

results = []
token = None
while True:
    if token:
        kwargs = {'NextPageToken': token}
    else:
        kwargs = {}
    data = cd.get_cost_and_usage(TimePeriod={'Start': start, 'End':  end}, Granularity='DAILY', Metrics=['UnblendedCost'], GroupBy=[{'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}, {'Type': 'DIMENSION', 'Key': 'SERVICE'}], **kwargs)
    results += data['ResultsByTime']
    token = data.get('NextPageToken')
    if not token:
        break


slack_results = []
fields_content = []
billing_date = ''
for result_by_time in results:
    for group in result_by_time['Groups']:
        amount = group['Metrics']['UnblendedCost']['Amount']
        unit = group['Metrics']['UnblendedCost']['Unit']
        billing_date = result_by_time['TimePeriod']['Start']
        fields_content.append(
            {
                'title': group['Keys'][1],
                'value': '$' + amount,
                'short': 'true'
            }
        )

slack_results.append(
    {
        'fallback':'',
        'color': 'good',
        'pretext': billing_date + 'の請求明細',
        'fields': fields_content
    }
)

# SlackにPOSTする内容をセット
payload_dic = {
    'attachments': slack_results,
    'channel': SLACK_ROOM,
    'username': '請求詳細',
    'icon_emoji': 'icon'
}

# SlackにPOST
r = requests.post(SLACK_URL, data=json.dumps(payload_dic))