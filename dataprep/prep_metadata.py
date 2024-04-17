import requests
import os
import datetime
import boto3
import pandas as pd
import numpy as np
import configparser

config_parser = configparser.ConfigParser()
config_parser.read("config.ini")
config=config_parser['DEFAULT']


DOWNLOAD_FILE = "dai-asllvd-BU_glossing_with_variations_HS_information-extended-urls-RU.xlsx"
DOWNLOAD_DIR = "data/raw/gloss2pose/"
URL = "http://www.bu.edu/asllrp/" + DOWNLOAD_FILE

def download_file(download_dir, download_filename, url):
    os.makedirs(download_dir, exist_ok=True)

    download_path = os.path.join(download_dir, download_filename)

    response = requests.get(url)

    with open(download_path, "wb") as file_obj:
        file_obj.write(response.content)

    return download_path

def clean_asllvd_metadata(from_filepath, to_filepath):
    """
    Writes asllvd excel file to a cleaned csv
    """
    video_set = pd.read_excel(from_filepath)
    video_set = video_set.replace("============", np.nan)
    video_set = video_set.replace("------------", np.nan)
    video_set = video_set.replace("-------------------------", np.nan)
    video_set = video_set.dropna(axis=0, subset=["Gloss Variant", "Session", "Scene", "Start", "End"], how="all")
    new_video_set = video_set[["Main New Gloss.1","Gloss Variant", "Consultant", "Session", "Scene", "Start", "End"]]
    new_video_set = new_video_set.sort_values(by=["Main New Gloss.1","Gloss Variant", "Consultant", "Session", "Scene", "Start", "End"])
    # print(video_set)
    # print(new_video_set)
    new_video_set = new_video_set.reset_index().drop(["index"], axis=1)
    new_video_set["id"] = new_video_set.index
    new_video_set["Scene"] = new_video_set["Scene"].astype(int)
    new_video_set["Start"] = new_video_set["Start"].astype(int)
    new_video_set["End"] = new_video_set["End"].astype(int)
    new_video_set["session_scene"] = new_video_set['Session'].apply(str)+"-"+new_video_set['Scene'].apply(str)
    new_video_set["Scene"].apply(lambda x: str(x))
    new_video_set["session_scene_id"] = (
        new_video_set["session_scene"]
    ).astype("category").cat.codes
    new_video_set["is_corrupt"] = 0
    new_video_set["Main New Gloss"]= new_video_set["Main New Gloss.1"].astype(str)
    new_video_set.to_csv(to_filepath, index=False)

    return to_filepath

def prep_metadata():
    s3_path=f"{config['s3_prefix']}/data/metadata/video_metadata.csv"
    csv_filepath = os.path.join(DOWNLOAD_DIR, "video_metadata.csv")
    filepath = download_file(DOWNLOAD_DIR, DOWNLOAD_FILE, URL)
    csv_filepath = clean_asllvd_metadata(filepath, csv_filepath)
    print("Uploading video_metadata to {}".format(s3_path))
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(config["s3_bucket"])
    #check if a bucket is exists, if not create a new bucket
    if bucket.creation_date is None:
        s3.create_bucket(Bucket=bucket)
    # Upload video metadata and timestamp
    bucket.upload_file(csv_filepath, s3_path)
    timestamp = s3.Object(config["s3_bucket"], s3_path + ".timestamp")
    timestamp.put(Body=r"{}".format(datetime.datetime.now()))

if __name__ == '__main__':
    prep_metadata()
