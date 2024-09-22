import multiprocessing
import os
import re
import subprocess
from multiprocessing import Process, Queue, Pipe
from threading import Thread

import boto3
from boto3.dynamodb.conditions import Key
import uuid
import pathlib

pose_bucket = "genasl-avatar"
asl_data_bucket = "genasl-data"
key_prefix = "gloss2posev6/lookup/"

pose_key_prefix = "gloss2posev6/lookup/pose"
sign_key_prefix = "gloss2posev6/lookup/sign"
table_name = 'Pose_Data6'


def lambda_handler(event, context):
    """.
    This function takes gloss sentence as input and split them by spaces to individual gloss
    and query DynamoDB to get the items matching gloss and returns a list of temporary signed URls as output
    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
        dict: Object containing details of the stock selling transaction
    """
    # Get the Gloss from event
    return gloss_to_video(event.get("Gloss"))


def gloss_to_video(gloss_sentence,pose_only=False, pre_sign=True):
    uniq_key = str(uuid.uuid4())

    sign_ids = []

    for gloss in gloss_sentence.split(" "):
        gloss = re.sub('[,!?.]', '', gloss.strip())
        # query dynamodb table
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        response = table.query(
            KeyConditionExpression=Key('Gloss').eq(gloss)
        )
        # for now pick the first item in the response
        if response['Count'] == 0:
            #if not sign found finger spell it
            for c in gloss:
                response = table.query(
                    KeyConditionExpression=Key('Gloss').eq(c)
                )
                if response['Count'] > 0:
                    sign_ids.append(response['Items'][0]['SignID'])
        else:
            sign_ids.append(response['Items'][0]['SignID'])
    # print(sign_ids)
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p1 = Thread(target=process_videos, args=(return_dict, "pose", sign_ids, uniq_key, pre_sign))
    p1.start()
    if not pose_only:
        p2 = Thread(target=process_videos, args=(return_dict, "sign", sign_ids, uniq_key, pre_sign))
        p2.start()
        p2.join()
    p1.join()
    if not pose_only:
        return {'PoseURL': return_dict["pose"],
                'SignURL': return_dict["sign"]}
    else:
        return {'PoseURL': return_dict["pose"]}


    # return {'PoseURL': process_vides("pose", sign_ids,uniq_key),
    #         'SignURL': process_vides("sign", sign_ids,uniq_key)}


def process_videos(return_dict, type, sign_ids, uniq_key,pre_sign):
    s3 = boto3.client('s3')
    temp_folder = f"/tmp/{uniq_key}/"
    pathlib.Path(os.path.dirname(temp_folder + f"{type}/")).mkdir(parents=True, exist_ok=True)

    with open(f"{temp_folder}{type}.txt", 'w') as writer:
        for sign_id in sign_ids:
            if type == "sign":
                key = f"{key_prefix}sign/sign-{sign_id}.mp4"
            else:
                key = f"{key_prefix}pose/pose-{sign_id}.mp4"
            local_file_name = f"{temp_folder}{type}/{type}-{sign_id}.mp4"
            s3.download_file(pose_bucket, key, local_file_name)
            writer.write(f"file '{local_file_name}' \n")
    # combine the sign videos
    #/opt/bin/
    cmd = f"/opt/homebrew/bin/ffmpeg  -f concat -safe 0 -i {temp_folder}{type}.txt -c copy {temp_folder}{type}.mp4"
    p1 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if pre_sign:
        s3.upload_file(f"{temp_folder}{type}.mp4", asl_data_bucket, f"{uniq_key}/{type}.mp4")
        video_url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': asl_data_bucket,
                'Key': f"{uniq_key}/{type}.mp4"
            },
            ExpiresIn=604800
        )
        return_dict[type] = video_url
        return video_url
    else:
        return_dict[type] = f"{temp_folder}{type}.mp4"
        return f"{temp_folder}{type}.mp4"


# def process_sign_video(sign_ids):
#     s3 = boto3.client('s3')
#     sign_list = []
#     sign_videos = []
#     for sign_id in sign_ids:
#         sign_key = f"{sign_key_prefix}/segment-{sign_id}.mp4"
#         presign_url = s3.generate_presigned_url(
#             ClientMethod='get_object',
#             Params={
#                 'Bucket': pose_bucket,
#                 'Key': sign_key
#             },
#             ExpiresIn=3600
#         )
#         # print(presign_url)
#         s3.download_file(pose_bucket, sign_key, f"{temp_folder}sign/sign-{sign_id}.mp4")
#         sign_videos.append(f"{temp_folder}sign/sign-{sign_id}.mp4")
#         sign_list.append({'Gloss': gloss, 'SignID': sign_id, 'SignURL': presign_url})
#     # combine the sign videos
#     with open(f"{temp_folder}sign.txt", 'w') as writer:
#         for video in sign_videos:
#             writer.write(f"file '{video}' \n")
#
#     cmd = f"/opt/bin/ffmpeg  -f concat -safe 0 -i {temp_folder}sign.txt -c copy {temp_folder}sign.mp4"
#     p1 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True)
#     s3.upload_file(temp_folder + "sign.mp4", asl_data_bucket, uniq_key + "sign.mp4")
#     sign_url = s3.generate_presigned_url(
#         ClientMethod='get_object',
#         Params={
#             'Bucket': asl_data_bucket,
#             'Key': uniq_key + "sign.mp4"
#         },
#         ExpiresIn=3600
#     )
#
# def process_pose_video(sign_ids):
#     pose_list = []
#     pose_videos = []
#     s3 = boto3.client('s3')
#     for sign_id in sign_ids:
#         pose_key = f"{pose_key_prefix}/pose-{sign_id}.mp4"
#         presign_url = s3.generate_presigned_url(
#             ClientMethod='get_object',
#             Params={
#                 'Bucket': pose_bucket,
#                 'Key': pose_key
#             },
#             ExpiresIn=3600
#         )
#         # print(presign_url)
#         s3.download_file(pose_bucket, pose_key, f"{temp_folder}pose/pose-{sign_id}.mp4")
#         pose_videos.append(f"{temp_folder}pose/pose-{sign_id}.mp4")
#
#         pose_list.append({'Gloss': gloss, 'SignID': sign_id, 'PoseURL': presign_url})
#     with open(f"{temp_folder}pose.txt", 'w') as writer:
#         for video in pose_videos:
#             writer.write(f"file '{video}' \n")
#     # combine pose videos
#     cmd = f"/opt/bin/ffmpeg -f concat -safe 0 -i {temp_folder}pose.txt -c copy {temp_folder}pose.mp4"
#     p1 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True)
#     s3.upload_file(temp_folder + "pose.mp4", asl_data_bucket, uniq_key + "pose.mp4")
#     pose_url = s3.generate_presigned_url(
#         ClientMethod='get_object',
#         Params={
#             'Bucket': asl_data_bucket,
#             'Key': uniq_key + "pose.mp4"
#         },
#         ExpiresIn=3600
#     )
#

if __name__ == "__main__":
    lambda_handler({"Gloss": "IX-1P NAME IX-1P SURESH"}, {})
