import os
import shutil
import time

import boto3
import requests
import pandas as pd
import subprocess
from botocore.exceptions import ClientError

import configparser

config_parser = configparser.ConfigParser()
config_parser.read("config.ini")
config = config_parser['DEFAULT']

CHECKPOINTS_DIR = "checkpoints/"
POSE_DIR = f"{config['s3_prefix']}/data/raw/gloss2pose/poses/"
VIDEO_DOWNLOAD_DIR = f"{config['s3_prefix']}/data/raw/gloss2pose/signs/"
VIDEO_METADATA_FILE = f"{config['s3_prefix']}/data/metadata/video_metadata.csv"
UNFORMATTED_URL = "http://csr.bu.edu/ftp/asl/asllvd/asl-data2/quicktime/{session}/scene{scene}-camera1.mov"
S3_BUCKET = config["s3_bucket"]  # replacce with your bucket name
partition_id = 0
number_partitions = 1
S3_LOOKUP_FOLDER = f"{config['s3_prefix']}/gloss2pose/lookup/"
DATA_DIR = os.getcwd()
FRAME_RATE = 30
boto3.setup_default_session(region_name=config['region'])
s3 = boto3.resource('s3')
bucket = s3.Bucket(S3_BUCKET)
dynamodb = boto3.resource('dynamodb')

def create_table_if_not_exists(table_name):
    try:
        # Check if the table exists
        response = boto3.client('dynamodb').describe_table(TableName=table_name)
        print(f"Table '{table_name}' already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Table does not exist, create a new one
            print(f"Table '{table_name}' does not exist. Creating a new table...")

            # Define the table schema
            table_schema = {
                'TableName': table_name,
                'KeySchema': [
                    {'AttributeName': 'Gloss', 'KeyType': 'HASH'},  # Partition_key
                    {'AttributeName': 'SignID', 'KeyType': 'RANGE'}  # Sort_key
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'Gloss', 'AttributeType': 'S'},
                    {'AttributeName': 'SignID', 'AttributeType': 'N'}
                ],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }

            # Create the table
            dynamodb.create_table(**table_schema)
            time.sleep(5)
            print(f"Table '{table_name}' created successfully.")
        else:
            print(f"An error occurred: {e}")


create_table_if_not_exists(config["table_name"])
table = dynamodb.Table(config["table_name"])


class VideoSegmentMetadata(object):
    def __init__(self, segment_id, start_frame, end_frame, gloss):
        self.segment_id = segment_id
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.gloss = gloss


class VideoMetadata(object):

    def __init__(self, video_id, url, session, scene, segments_metadata):
        self.video_id = video_id
        self.url = url
        self.session = session
        self.scene = scene
        self.segments_metadata = segments_metadata


def get_video_metadata(bucket, s3_filepath, download_filepath, partition, num_partitions):
    print(s3_filepath)
    os.makedirs(os.path.dirname(download_filepath), exist_ok=True)
    bucket.download_file(s3_filepath, download_filepath)
    metadata = pd.read_csv(s3_filepath)
    print(metadata)
    metadata = metadata[metadata["session_scene_id"] % num_partitions == partition]
    # Remove corrupt segments
    metadata = metadata[metadata["is_corrupt"] == 0]
    # Keep only Liz videos
    metadata = metadata[metadata["Consultant"] == "Liz"]
    collapsed_metadata = metadata[["session_scene_id", "Session", "Scene"]].drop_duplicates().sort_values(
        by=["session_scene_id"])
    collapsed_metadata.index = collapsed_metadata["session_scene_id"]
    metadata["id-start-end-gloss"] = metadata["id"].apply(str) + "$" + \
                                     metadata["Start"].apply(str) + "$" + \
                                     metadata["End"].apply(str) + "$" + \
                                     metadata["Gloss Variant"]
    frames_info = metadata.groupby(["session_scene_id"])["id-start-end-gloss"].apply(list)
    collapsed_metadata = pd.concat([collapsed_metadata, frames_info], axis=1)
    return [
        VideoMetadata(
            value[0],
            UNFORMATTED_URL.format(
                session=value[1],
                scene=value[2]
            ),
            value[1],
            value[2],
            sorted([
                VideoSegmentMetadata(
                    segment_id=int(segment.split("$")[0]),
                    start_frame=int(segment.split("$")[1]),
                    end_frame=int(segment.split("$")[2]),
                    gloss=segment.split("$")[3]
                ) for segment in value[3]
            ], key=lambda x: x.start_frame)
        ) for value in collapsed_metadata.values
    ]


def process_video(video, checkpoint_video_id,checkpoint_filepath):
    # Skip all videos with id <= checkpoint_video_id
    # If checkpoint_video_id isn't found, raise an Exception
    if checkpoint_video_id is None:
        pass
    elif checkpoint_video_id > video.video_id:
        return
    elif checkpoint_video_id == video.video_id:
        checkpoint_video_id = None
        return
    else:
        raise Exception(
            "Checkpoint video_id {} not valid".format(checkpoint_video_id)
        )
    print("Downloading {} with video_id {}".format(video.url, video.video_id))
    download_dir = os.path.join(DATA_DIR, VIDEO_DOWNLOAD_DIR)
    video_filepath = download_large_file(
        video.url,
        download_dir,
        "{}-{}.{}".format(
            video.session,
            video.scene,
            video.url.split(".")[-1]
        )
    )
    for segment in video.segments_metadata:
        print("Processing video segment {}".format(
            segment.segment_id
        ))
        temp_segment_filepath = clip_video(
            video_filepath,
            os.path.join(
                download_dir,
                "temp-segment-{}.mov".format(segment.segment_id)
            ),
            segment.start_frame,
            segment.end_frame,
        )

        segment_filepath = resample_video(
            temp_segment_filepath,
            os.path.join(
                download_dir,
                "sign-{}.mp4".format(segment.segment_id)
            ),
            FRAME_RATE
        )

        if os.path.exists(segment_filepath):
            bucket.upload_file(
                segment_filepath,
                os.path.join(
                    S3_LOOKUP_FOLDER,
                    "sign/",
                    os.path.basename(segment_filepath)
                )
            )

        if os.path.exists(temp_segment_filepath):
            bucket.upload_file(
                temp_segment_filepath,
                os.path.join(
                    S3_LOOKUP_FOLDER,
                    "rawsign/",
                    os.path.basename(temp_segment_filepath)
                )
            )

        gloss = segment.gloss.upper()
        for g in gloss.split('/'):
            g = g.replace('+', '')
            g = g.replace('#', '')
            response = table.put_item(
                Item={
                    'Gloss': g,
                    'SignID': segment.segment_id
                }
            )

        # Clean up
        os.remove(temp_segment_filepath)
        if os.path.exists(segment_filepath):
            os.remove(segment_filepath)

    # Update checkpoint after processing entire video
    checkpoint = s3.Object(S3_BUCKET, checkpoint_filepath)
    checkpoint.put(Body=r'{}'.format(video.video_id))
    os.remove(video_filepath)


def run_bash_cmd(cmd, dir=None):
    subprocess.run(cmd, shell=False, cwd=dir, capture_output=True, text=True)


def clip_video(from_video_filepath, to_video_filepath, start_frame, end_frame):
    """
    create video clip starting at @start_frame and ending at @end_frame inclusive
    """

    unformatted_cmd = "ffmpeg -i {from_path} -vf trim=start_frame={start_frame}:end_frame={end_frame} -y -an {to_path}"

    cmd = unformatted_cmd.format(
        from_path=from_video_filepath,
        to_path=to_video_filepath,
        start_frame=start_frame,
        end_frame=end_frame + 1,
    )

    run_bash_cmd(cmd)

    return to_video_filepath


def resample_video(from_video_filepath, to_video_filepath, frame_rate):
    """
    resamples video with @frame_rate and outputs new video
    """

    unformatted_cmd = "ffmpeg -i {from_path} -filter:v fps={frame_rate} -q:v 0 -vcodec h264  -y {to_path}"

    cmd = unformatted_cmd.format(
        from_path=from_video_filepath,
        to_path=to_video_filepath,
        frame_rate=frame_rate,
    )

    run_bash_cmd(cmd)

    return to_video_filepath


# taken from https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
def download_large_file(url, download_dir, filename):
    os.makedirs(download_dir, exist_ok=True)
    local_filename = os.path.join(download_dir, filename)
    with requests.get(url, stream=True) as response:
        with open(local_filename, 'wb') as file_obj:
            shutil.copyfileobj(response.raw, file_obj)

    return local_filename


def create_sign_videos():
    checkpoint_filename = "partition-{}-of-{}.txt".format(
        partition_id,
        number_partitions
    )

    checkpoint_filepath = os.path.join(
        S3_LOOKUP_FOLDER,
        CHECKPOINTS_DIR,
        checkpoint_filename
    )

    try:
        checkpoint_video_id = s3.Object(
            S3_BUCKET, checkpoint_filepath
        ).get()['Body'].read().decode('utf-8')
        checkpoint_video_id = int(checkpoint_video_id)
    except s3.meta.client.exceptions.NoSuchKey:
        checkpoint_video_id = None

    video_metadata_filepath = os.path.join(
        DATA_DIR,
        VIDEO_METADATA_FILE
    )

    videos = get_video_metadata(
        bucket, VIDEO_METADATA_FILE, video_metadata_filepath,
        partition_id, number_partitions
    )
    for video in videos:
        process_video(video, checkpoint_video_id,checkpoint_filepath)


if __name__ == '__main__':
    create_sign_videos()
