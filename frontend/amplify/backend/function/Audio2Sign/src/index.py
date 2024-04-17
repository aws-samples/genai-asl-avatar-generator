import json
import boto3
import time
import logging

def handler(event, context):
    print('received event:')
    print(event)
    # invoke step function
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    sfn_client = boto3.client('stepfunctions')
    if "Text" in event["queryStringParameters"]:
        input=json.dumps({"Text": event["queryStringParameters"]["Text"]})
    else:
        input=json.dumps({
                        "BucketName": event["queryStringParameters"]["BucketName"],
                        "KeyName":event["queryStringParameters"]["KeyName"] }) 
    sfn_execution_arn = sfn_client.start_execution(
        stateMachineArn='arn:aws:states:us-west-2:853513360253:stateMachine:GenASLAvatarStateMachine-KOBckdHnbr3S',
        input=input
    ).get('executionArn')
    logger.info({'stateMachineArn': sfn_execution_arn})
 
  
    exec_response=sfn_client.describe_execution(executionArn=sfn_execution_arn)
    while exec_response.get('status') == 'RUNNING':
        time.sleep(5)
        exec_response=sfn_client.describe_execution(executionArn=sfn_execution_arn)

    if (exec_response.get('status') == 'SUCCEEDED'):
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
            },
            'body': exec_response['output']
        }
    else:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'Error': exec_response['error'],
                                'Reason': exec_response['cause'],}) 
        }

        