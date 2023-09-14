import os
import json
import boto3

region = os.environ['AWS_REGION']

sfClient = boto3.client('stepfunctions', region_name=region)

def lambda_handler(event, context):
    print(event)

    taskToken = event['TaskToken']

    try:
        sfClient.send_task_success(
            taskToken=taskToken,
            output=json.dumps({'result': event['result']})
        )
    except Exception as e:
        print(e)
        sfClient.send_task_failure(
            taskToken=taskToken,
            error=str(e)
        )
    return {
        'statusCode': 202
    }
