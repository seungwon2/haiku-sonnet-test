
import boto3
import json
import os

client = boto3.client('stepfunctions')
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    input = {
        "Bucket": bucket,
        "Key": key
    }

    response = client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input = json.dumps(input)
    )

    return json.dumps(response, default=str)