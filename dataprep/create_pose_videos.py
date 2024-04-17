import concurrent

import configparser

config_parser = configparser.ConfigParser()
config_parser.read("config.ini")
config = config_parser['DEFAULT']
f"{config['s3_prefix']}/gloss2pose/lookup/"

bucket_name=config['s3_bucket']
from_key=f"{config['s3_prefix']}/gloss2pose/lookup/sign/"
to_key=f"{config['s3_prefix']}/gloss2pose/lookup/pose/"


import os
import pathlib


import boto3 as boto3

os.chdir("mmpose")

import mmcv
from mmengine.registry import init_default_scope
import numpy as np

from mmpose.apis import inference_topdown
from mmpose.apis import init_model as init_pose_estimator
from mmpose.evaluation.functional import nms
from mmpose.registry import VISUALIZERS
from mmpose.structures import merge_data_samples
import tempfile
import cv2

try:
    from mmdet.apis import inference_detector, init_detector
    has_mmdet = True
except (ImportError, ModuleNotFoundError):
    has_mmdet = False


# pose_config = 'configs/body_2d_keypoint/topdown_heatmap/coco/td-hm_hrnet-w32_8xb64-210e_coco-256x192.py'
pose_config = 'configs/wholebody_2d_keypoint/rtmpose/coco-wholebody/rtmpose-l_8xb32-270e_coco-wholebody-384x288.py'
# pose_config ='configs/_base_/datasets/coco_wholebody_openpose.py'
pose_checkpoint = '../checkpoints/rtmpose-l_simcc-coco-wholebody_pt-aic-coco_270e-384x288-eaeb96c8_20230125.pth'
# pose_checkpoint = 'checkpoints/rtmpose-x_simcc-coco-wholebody_pt-body7_270e-384x288-401dfc90_20230629.pth'
det_config = 'demo/mmdetection_cfg/faster_rcnn_r50_fpn_coco.py'
det_checkpoint = '../checkpoints/faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth'

device = 'cuda:0'
cfg_options = dict(model=dict(test_cfg=dict(output_heatmaps=True)))

# build detector
detector = init_detector(
    det_config,
    det_checkpoint,
    device=device
)

# build pose estimator
pose_estimator = init_pose_estimator(
    pose_config,
    pose_checkpoint,
    device=device,
    cfg_options=cfg_options
)

# init visualizer
pose_estimator.cfg.visualizer.radius = 3
pose_estimator.cfg.visualizer.line_width = 5
visualizer = VISUALIZERS.build(pose_estimator.cfg.visualizer)
# the dataset_meta is loaded from the checkpoint and
# then pass to the model in init_pose_estimator
visualizer.set_dataset_meta(pose_estimator.dataset_meta, skeleton_style='openpose')


def visualize_img(img_path, detector, pose_estimator, visualizer,
                  show_interval, out_file, skeleton_style):
    """Visualize predicted keypoints (and heatmaps) of one image."""

    # predict bbox
    scope = detector.cfg.get('default_scope', 'mmdet')
    if scope is not None:
        init_default_scope(scope)
    detect_result = inference_detector(detector, img_path)
    pred_instance = detect_result.pred_instances.cpu().numpy()
    bboxes = np.concatenate(
        (pred_instance.bboxes, pred_instance.scores[:, None]), axis=1)
    bboxes = bboxes[np.logical_and(pred_instance.labels == 0,
                                   pred_instance.scores > 0.3)]
    bboxes = bboxes[nms(bboxes, 0.3)][:, :4]

    # predict keypoints
    pose_results = inference_topdown(pose_estimator, img_path, bboxes)
    data_samples = merge_data_samples(pose_results)
    # show the results
    inp_img = mmcv.imread(img_path, channel_order='rgb')
    # create a black image
    # create a black image
    img = np.zeros(inp_img.shape, dtype=np.uint8)
    # print(pose_estimator.dataset_meta)
    visualizer.add_datasample(
        'result',
        img,
        data_sample=data_samples,
        draw_gt=False,
        draw_heatmap=False,
        draw_bbox=False,
        show=False,
        wait_time=show_interval,
        skeleton_style=skeleton_style,
        out_file=out_file,
        kpt_thr=0.3)


def create_video(input_video,output_file):
    cap = cv2.VideoCapture(input_video)
    video_writer = None
    pred_instances_list = []
    frame_idx = 0

    while cap.isOpened():
        success, frame = cap.read()
        frame_idx += 1

        if not success:
            break

        # topdown pose estimation
        pred_instances = visualize_img(
            frame,
            detector,
            pose_estimator,
            visualizer,
            show_interval=0,
            out_file=None,
            skeleton_style='openpose')

        # output videos
        if output_file:
            frame_vis = visualizer.get_image()

            if video_writer is None:
                fourcc = cv2.VideoWriter_fourcc(*'X264')
                # the size of the image with visualization may vary
                # depending on the presence of heatmaps
                video_writer = cv2.VideoWriter(
                    output_file,
                    fourcc,
                    30,  # saved fps
                    (frame_vis.shape[1], frame_vis.shape[0]))

            video_writer.write(mmcv.rgb2bgr(frame_vis))

    if video_writer:
        video_writer.release()

    cap.release()

def create_image():
    img = '../test/sureshsahana.jpg'
    visualize_img(
        img,
        detector,
        pose_estimator,
        visualizer,
        show_interval=0,
        out_file=None,
        skeleton_style='openpose')

    vis_result = visualizer.get_image()

    with tempfile.TemporaryDirectory() as tmpdir:
        file_name = '../test/pose_results.png'
        cv2.imwrite(file_name, vis_result[:, :, ::-1])



s3 = boto3.resource('s3')
s3_client= boto3.client('s3')

def process_file(summary_data):
    keyname=summary_data.key
    #write code to download file from S3 and process it and upload it back to S3
    s3 = boto3.client('s3')
    source_file= "C:\\Temp\\"+ keyname.replace("/","\\")
    pathlib.Path(os.path.dirname(source_file)).mkdir(parents=True, exist_ok=True)
    print(source_file)
    s3.download_file(bucket_name, keyname, source_file)
    to_file= source_file.replace("sign","pose")
    pathlib.Path(os.path.dirname(to_file)).mkdir(parents=True, exist_ok=True)
    create_video(source_file,to_file)
    #upload processed file back to S3
    s3.upload_file(to_file, bucket_name, to_key+ os.path.basename(to_file))
    print(f"uploaded file {to_key+ os.path.basename(to_file)}")
    #delete local filel file
    os.remove(to_file)
    os.remove(source_file)

    return "processed"

def convert():
    bucket = s3.Bucket(bucket_name)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(process_file, bucket.objects.filter(Prefix=from_key))


if __name__ == '__main__':
    convert()
   # create_image()
   # create_video("../test/hello.mp4","../test/sigh.mp4")

