import json

import boto3


def construct_query(text):
    return f"""

Human: Here are some examples of translations from english text to ASL gloss 
Examples:
Apples ==> APPLE
you  ==> IX-2P
your  ==> IX-2P
Love ==> LIKE
My ==> IX-1P
Thanks ==> THANK-YOU
am ==> 
and ==> 
be ==>
of ==>
video ==> MOVIE
image ==> PICTURE
conversations ==> TALK
type of ==> TYPE
? ==> QUESTION
Watch ==> SEE

Translate the following english text to ASL Gloss and surround it  with tags <gloss> and </gloss>.
{text} ==>


Assistant:"""


def lambda_handler(event, context):
    """Invoke Bedrock to convert English text to ASL Gloss
    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function
    context: object, required
        Lambda Context runtime methods and attributes
    Returns
    ------
        dict: text consists of ASL Gloss
    """
    #

    return {'Gloss': text_to_asl_gloss(event.get("Text"))}


def text_to_asl_gloss(text):
    bedrock_client = boto3.client(service_name="bedrock-runtime")
    # create the prompt

    prompt_data = construct_query(text)

    # body = json.dumps({
    #     "prompt": prompt_data,
    #     "max_tokens_to_sample": 100,
    #     "temperature": 0.1,
    #     "top_k": 250,
    #     "top_p": 0.5,
    #     "stop_sequences": []
    # })

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "temperature": 0.1,
        "top_k": 250,
        "top_p": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt_data}],
            }
        ],
    }

    modelId = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock_client.invoke_model(body=json.dumps(body),
                                           modelId=modelId,
                                           accept=accept,
                                           contentType=contentType)
    response_body = json.loads(response.get('body').read())

    output_text = response_body['content'][0]['text']
    print(response_body)
    sub1 = '<gloss>'
    sub2 = '</gloss>'
    idx1 = output_text.find(sub1)
    idx2 = output_text.find(sub2)
    # length of substring 1 is added to
    # get string from next character
    gloss = output_text[idx1 + len(sub1) + 1: idx2]
    print(gloss)
    return gloss


if __name__ == "__main__":
    lambda_handler({"Text": "what is your name"}, {})
    lambda_handler({"Text": "How are you?"}, {})
    lambda_handler({"Text": "She is watching a movie"}, {})
    lambda_handler({"Text": "He wants to play"}, {})
    lambda_handler({"Text": "Can you come with me?"}, {})
