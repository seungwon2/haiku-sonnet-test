import boto3
import base64
import json

s3 = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    # S3 버킷과 객체 키를 이벤트에서 추출
    bucket_name = event['Bucket']
    object_key = event['Key']
    # 시스템 프롬프트
    prompt = """ You are a highly skilled translator with expertise in many languages. 
    Your task is to identify the language of the text I provide and accurately translate it into the Korean while preserving the meaning, tone, and nuance of the original text. 
    Please maintain proper grammar, spelling, and punctuation in the translated version.
    
    """

    # S3 객체 다운로드
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    content = response['Body'].read().decode('utf-8')

    
    # content = "Few-shot translation performance on 6 language pairs as model capacity increases. There is a consistent trend of improvement across all datasets as the model scales, and as well as tendency for translation into English to be stronger than translation from English."
    
    # Bedrock 호출을 위한 Payload 작성, 원하는 결과가 나오도록 모델 파라미터를 변경할 수 있습니다.
    payload = {
        "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
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
    haiku_result = response_body['content'][0]['text']

    # sonnet에게 넘겨줄 응답 정리
    result = {}
    result['haiku'] = haiku_result
    result['content'] = content
    result['key'] = object_key
    # 만약, 전체 응답이 필요하다면 response_body 만 리턴되도록 해주세요.
    
    return result