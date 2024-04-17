import json

import boto3
import requests as requests


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
    job_name=event.get("TranscriptionJobName")
    #get the transcription job
    transcribe = boto3.client('transcribe')
    job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    #get the output from the transcription job
    output_uri = job.get("TranscriptionJob").get("Transcript").get("TranscriptFileUri")
    print(output_uri)
    response = requests.get(output_uri)
    #get content from the response
    json_text = json.loads(response.content)
    #get the output from the json
    output = json_text.get("results").get("transcripts")[0].get("transcript")
    return {"Text":output}