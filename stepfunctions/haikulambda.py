import boto3
import base64
import json
import csv
import re
import time

s3 = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')


def translate(text, glossary):
    word_dict = {}
    for line in glossary.split('\n'):
        if line.strip():  # 빈 줄이 아닌 경우에만 처리
            word, translation = line.split('\t')
            word_dict[word] = translation
            word_dict[translation] = word

    words = text.split()
    translated_words = [word_dict.get(word, word) for word in words]
    translated_text = ' '.join(translated_words)

    return translated_text
    
def load_json_from_s3(bucket_name, file_key):
    # S3 클라이언트 생성
    s3 = boto3.client('s3')

    try:
        # S3에서 파일 내용 가져오기
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        # JSON 데이터 로드
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        return json_data  # JSON 데이터로 파싱하여 반환
    except Exception as e:
        print(f"Error loading JSON from S3: {e}")
        return None
        
def process_json(bucket_name, file_key):
    # JSON 파싱
    json_data = load_json_from_s3(bucket_name, file_key)

    if json_data:
        # 결과 문장 리스트 초기화
        sentences = []

        # 각 subtitles에 대해 처리
        for idx, subtitle in enumerate(json_data['subtitles']):
            # candidates 추출
            candidates = subtitle['candidates']
            # transcript 추출하여 문장으로 만들기
            sentence = " ".join(candidate['transcript'] for candidate in candidates if candidate['transcript'])
            # 문장이 존재하면 문장 리스트에 추가
            if sentence:
                sentences.append(f"[{idx+1}] {sentence}")

        # 결과 반환
        return sentences
    else:
        return None

def split_into_paragraphs(text, lines_per_paragraph=20):
    paragraphs = []
    lines = text.split(".")
    for i in range(0, len(lines), lines_per_paragraph):
        paragraph = "\n".join(lines[i:i+lines_per_paragraph])
        paragraphs.append(paragraph)
    return paragraphs

def lambda_handler(event, context):
    
    # S3 버킷과 객체 키를 이벤트에서 추출
    bucket_name = event['Bucket']
    object_key = event['Key']
    
    glossary_file = s3.get_object(Bucket='voithrustack-contentsbucket75f5c3bf-9h3vsoi31bms', Key='enko-glossary.tsv')

    glossary = glossary_file['Body'].read().decode('utf-8')

    # 시스템 프롬프트
    prompt = f""" You are a highly skilled reader with expertise in many languages.
    I will provide you with the entire content of a lecture.
    Provide an analysis of the speaker's tone and characteristics, a summary of the content, and information that can be referenced when translating this lecture.
    
    Follow these steps for translating the lecture:
    step 1: Read all the lecture content
    step 2: Create a summary of the lecture content
    step 3: Analyze the characteristics of the speaker
    step 4: As a translator, create notes to reference when translating
    
    Write the <output> in the following format:
    
    <output>
    {{
        "summary": "", # Summary of the lecture content
        "speaker": "", # Analysis of the speaker's characteristics
        "reference": "" # Notes to reference when translating
    }}
    </output>

    """

    # S3 객체 다운로드
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    content = response['Body'].read().decode('utf-8')
    
    original_contents = process_json(bucket_name, object_key)
    combined_original_contents = ''.join(original_contents)
    reflect_glossary = translate(combined_original_contents, glossary)  # 수정된 부분

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
                            "text": combined_original_contents
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
    start_index = haiku_result.find("{")
    end_index = haiku_result.rfind("}")
    haiku_result = haiku_result[start_index:end_index+1]
    
    # sonnet에게 넘겨줄 응답 정리
    result = {}
    result['haiku'] = haiku_result
    result['content'] = reflect_glossary
    result['key'] = object_key
    
    result_array = []
    
    lines_per_chunk = 30
    for chunk in split_into_paragraphs(reflect_glossary, 20):
        # print("chunk: ", chunk)

        chunk = chunk.replace("\n", " ")
        result_chunk = {
            'haiku': haiku_result,
            'content': chunk,
            'key': object_key
        }
        result_array.append(result_chunk)

    return result_array
