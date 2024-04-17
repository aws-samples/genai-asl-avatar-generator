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
Me ==> IX-1P
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

Translate following english text to ASL Gloss  
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
    text = event.get("Text")
    bedrock_client = boto3.client(service_name="bedrock-runtime")
    # create the prompt

    prompt_data = construct_query(text)

    body = json.dumps({
        "prompt": prompt_data,
        "max_tokens_to_sample": 100,
        "temperature": 0.1,
        "top_k": 250,
        "top_p": 0.5,
        "stop_sequences": []
    })

    modelId = 'anthropic.claude-v2'
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock_client.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())

    outputText = response_body.get('completion')
    print(response_body)
    if "\n" in outputText:
        gloss = outputText[outputText.rindex('\n') + 1:]
    else:
        gloss = outputText
    if "==>" in gloss:
        gloss = gloss[gloss.rindex("==>") + 3:]

    print(gloss)
    return {'Gloss': gloss.strip()}


if __name__ == "__main__":
    lambda_handler({"Text": "what is your name"}, {})
