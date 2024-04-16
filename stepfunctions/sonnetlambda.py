import boto3
import os
import json

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    # # 앞선 haiku 모델의 응답

    haiku = event['haiku']
    # # 원문
    content = event['content']
    

    prompt = f"""
    You are a highly skilled subtitle translator with expertise in many languages. 
    Your task is to translate a portion of the given lecture into Korean, while preserving the meaning, tone, and nuance of the original text. 
    When working, you must follow the given <caution>, refer to <full_lecture> which summarizes the overall context of the lecture, and <example>.
    
    <caution>
    1. Preserving the number of sentences
    2. The numbers enclosed in [] indicate the timing of each subtitle. 
    3. The translation should be arranged such that sentences with the same meaning correspond based on the [] markers.
    4. Remove unnecessary pronouns.
    </caution>
    
    
    <full_lecture>
    {haiku}
    </full_lecture>
    
    <example1>
    <original_contents>
    However, the complex thought systems of Buddhism and Confucianism, just hearing the names can be mind-boggling,[[1]]so I had no choice but to provide a lengthy explanation[[2]]to aid in basic understanding.[[3]]Now, I will delve into the content[[4]]that will be covered in weeks 8 and 9.[[5]]As I mentioned earlier,[[6]]the three religions of Confucianism, Buddhism, and Taoism, which were introduced to the Korean Peninsula during the Three Kingdoms Period,[[7]]have rooted, fruited, and developed in the Korean intellectual system[[8]]over a thousand years.[[9]]
    </original_contents>
    <output>
    {{"contents" : "불교와 유교, 이름만 들어도 머리가 지끈거리는[[1]]이 사유 체계에 대한 기본적인 이해를 도와주기 위해[[2]]어쩔 수 없이 설명이 많이 길어졌습니다.[[3]]이제부터는 본격적으로[[4]]8, 9주차에서 다룰 내용에 대해 이야기를 해 볼까 합니다.[[5]]지금까지 말씀드린 것처럼[[6]]삼국시대에 한반도로 유입된 유불도 삼교는[[7]]천여년의 세월을 거쳐 한민족의 사유체계에 뿌리를 내리고[[8]]열매를 맺으며 발전하였습니다[[9]]"}}
    </output>
    </example1>
    <example2>
    <original_contents>
    Then, let's open it up[[1]]Before opening this, I'll first set up the Sequencer[[2]]and put it in the folder[[3]]Also, I think I need to align the Ribbon progress and location here[[4]]I'll give a Key value at frame 40 for the Spawn[[5]]Then, I'll release it from the previous frame and the location value will be positioned on the 700 character side, but instead, there's a center here, I'll create a Chain that stretches out long like this[[6]]Using the Beam Particle, to align with the magic circle, it should be positioned right here[[7]]Therefore, I'll rotate the Rotation by about 60°[[8]]And then, I think I need to create Activate Deactivate as well[[9]]So, I'll create a Niagara Component and at frame 208, just like the Sphere or Magic Circle we made last time, I'll pull out the FX System Toggle Track and give it an Activate Key value, and at 210, I'll Deactivate it[[10]]Deactivate is also included, so conversely, we need two of them[[11]]Since it needs to come out on both sides, I'll copy it as number 2 and just twist the location value to a minus direction[[12]]Shall we take a look[[13]]It's coming out here now[[14]]First, I'll adjust it within the Particle to be generated on this side[[15]]Firstly, after setting up the Particle, I'll adjust the meeting point with the Ribbon Trail[[16]]So, here we only need three[[17]]So, I'll delete Glow_03[[18]]
    </original_contents>
    <output>
    {{
        "contents": "그러면 열어보겠습니다[[1]]이거를 먼저 여는 것보다 일단 Sequencer에 먼저 세팅을 할게요[[2]]폴더에 넣어주고요[[3]]그리고 여기 Ribbon 진행되는 거하고 위치도 한번 맞춰야 될 것 같거든요[[4]]Spawn은 40프레임에 Key 값을 줄게요[[5]]그리고 이전 프레임에서 해제하고 그리고 위치값은 700 캐릭터 쪽에 위치할 거기 때문에 대신에 여기에 센터가 있지만 이렇게 길게 뻗어나가는 식의 Chain을 만들 거예요[[6]]Beam Particle을 이용해서 위치값은 마법진에 맞추려면 여기 부분에 위치해야겠죠[[7]]그렇기 때문에 Rotation을 60° 정도 돌려줄게요[[8]]그리고 그다음에 Activate Dectivate도\n만들어야 될 것 같거든요[[9]]그래서 Niagara Component 만들어주고 208 프레임에 저번 시간에 만들었던 Sphere나 Magic Circle처럼 동일한 프레임으로 FX System Toggle Track을 꺼내서 Activate Key 값 주고 210에 Dectivate 시키겠습니다[[10]]Dectivate도 들어가 있고 그렇다면 반대로 두 개가 필요한 거죠[[11]]양쪽에 나와야 되기 때문에 복사한 거는 2번으로 해서 위치값만 방향을 마이너스 값으로 틀어 줄게요[[12]]한 번 볼까요[[13]]지금은 여기 나오고 있죠[[14]]일단 이쪽에 생성되게 Particle 안에서 조정을 할 거거든요[[15]]일단 1차적으로 Particle을 세팅을 한 다음에 Ribbon Trail하고 만나는 지점을 조정을 해 볼게요[[16]]그러면 여기서 필요한 거는 3개만 쓸 거거든요[[17]]그래서 Glow_03은 지우겠습니다[[18]]"
    }}
    </output>
    </example2>
    <example3>
    <original_contents>
    It seems to fit quite well like this[[1]]I think it fits well enough[[2]]To make it a bit more precise, adjusting to this extent would be better[[3]]Then, I've made some more adjustments to align with the connecting lines[[4]]And it's coming out well, fitting into this magic circle shape[[5]]Here, the magic circle is being drawn more like the line above[[6]]These are the parts that need to be organized[[7]]It seems better to press this MagicCircle part and raise the Chain with Sort[[8]]I'll raise the Chain to number 3[[9]]Then it will be drawn above here[[10]]The shape fits perfectly[[11]]Then a black hole is created here on the Ribbon, and it seems to cover the Ribbon well[[12]]It's created, so from here, we can try making additional characters connected by chains[[13]]I will turn off this Particle[[14]]Save, and the things we modified here will be stored in the Sequencer[[15]]Those not in the Sequencer will need to be adjusted at the Level[[16]]Then, let's add the Beam chain-like effect[[17]]Since the Beam is also going to be represented when it's created, I plan to use a very short Ribbon Particle together[[18]]
    </original_contents>
    <output>
    {{
        "contents": "비슷하게 잘 맞는 것 같거든요[[1]]이 정도면 잘 맞는 것 같아요[[2]]살짝 더 정확하게 해 주려면 이 정도로 맞추면 더 좋을 것 같네요[[3]]그러면 연결선까지 조금 더 맞춰서 수정을 했고요[[4]]그리고 이 마법진 모양에 맞춰서 잘 나오고 있죠[[5]]여기 마법진이 더 위에 선처럼 그려지고 있죠[[6]]이런 부분을 정리를 해 줘야겠죠[[7]]이 MagicCircle 부분을 눌러서 Sort로 Chain을 올려주는 게 나을 것 같네요[[8]]Chain을 3번으로 올려줄게요[[9]]그러면 여기 위에 그려지죠[[10]]모양이 딱 맞춰서 들어가 있어요[[11]]그러면 여기 Ribbon에 블랙홀이 생성이 되고 그러면 Ribbon도 잘 가려지는 것 같죠[[12]]생성이 돼서 여기서부터 사슬이 연결되게 캐릭터로 추가로 제작을 해 보면 될 것 같아요[[13]]이 Particle은 꺼주겠습니다[[14]]Save 하고 여기 옵션 수정해 줬던 것들은 여기에 Sequencer에 저장이 될 거예요[[15]]Sequencer에 없는 것들은 Level로 조정을 해야겠죠[[16]]그러면 이어서 Beam 사슬 느낌의 이펙트까지 추가해 볼게요[[17]]Beam이 생성되는 것도 표현을 할 거기 때문에 생성될 때 아주 짧은 Ribbon Particle도 같이 사용을 할 예정이거든요[[18]]" 
    }}
    </output>
    </example3>
    
    Follow these steps for the translation task:
    1. First, read <full_lecture> and examine the overall context of this lecture and the characteristics of the speaker.
    2. Read <caution> and familiarize yourself with the points to be cautious about when translating.
    3. Proceed with the translation.
    4. After translating, review the translated sentences to ensure they reflect the content of <caution>, and rewrite any insufficient parts.
    5. Format your final output using the provided output format.

    
    <output>
    {{
        "contents": "",
    }}
    </output>
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

    start_index = result.find("{")
    end_index = result.rfind("}")
    result = result[start_index:end_index+1]
    result = json.dumps(result, ensure_ascii=False)
    
    # Sonnet의 응답만 파일로 저장
    print(result)
    
    return result