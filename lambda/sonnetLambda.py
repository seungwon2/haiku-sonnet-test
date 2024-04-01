import boto3
import os
import json

bucket_name = os.environ['RESULT_BUCKET']

s3 = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    # 앞선 haiku 모델의 응답
    haiku = event['haiku']
    # 원문
    content = event['content']
    # 파일 이름
    key = event['key']
    file_key = f'test/eng-ko/{key}'

    prompt = """ You are a highly skilled translator with expertise in many languages. 
    Your task is to identify the language of the text I provide and accurately translate it into the Korean while preserving the meaning, tone, and nuance of the original text. 
    Please maintain proper grammar, spelling, and punctuation in the translated version.
    
    """

    # Bedrock 호출을 위한 Payload 작성, 원하는 결과가 나오도록 모델 파라미터를 변경할 수 있습니다.
    payload = {
        "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
        "contentType": "application/json",
        "accept": "application/json",
        "body": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "top_k": 250,
            "top_p": 0.999,
            "temperature": 0,
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                }
            ]
        }
    }
    
    # Convert the payload to bytes
    body_bytes = json.dumps(payload['body']).encode('utf-8')
    
    # Invoke the model
    response = bedrock_runtime.invoke_model(
        body=body_bytes,
        contentType=payload['contentType'],
        accept=payload['accept'],
        modelId=payload['modelId']
    )
    
    # Process the response
    response_body = json.loads(response['body'].read())
    result = response_body['content'][0]['text']
    
    # Sonnet의 응답만 파일로 저장
    print(result)
    s3.put_object(Bucket=bucket_name, Key=file_key, Body=result)
    
    return result