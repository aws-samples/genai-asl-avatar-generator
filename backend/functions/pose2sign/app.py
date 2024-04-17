import json

import boto3


def lambda_handler(event, context):
    """
    Write a function to get the output from AWS Transcription Job
    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function
    context: object, required
        Lambda Context runtime methods and attributes
    Returns
    ------
        String: Audio to text transcription created by transcription job
    """
