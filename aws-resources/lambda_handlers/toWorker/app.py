# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
import boto3


TOPIC = os.environ['WORKER_TOPIC'] # <<<<<<<<<<<<<<

region_name = "eu-central-1"
client = boto3.client('iot-data', region_name=region_name)

def lambda_handler(event, context):
    print("Starting the function")

    message_topic = TOPIC
    message_json = json.dumps(event)

    response = client.publish(
        topic=message_topic,
        qos=1,
        payload=message_json
    )

    return {"statusCode": 200, "body": json.dumps(response)}
