# check NVCC version
nvcc -V

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
mim install "mmdet>=3.0.0"
pip install git+https://github.com/jin-s13/xtcocoapi


git clone https://github.com/open-mmlab/mmpose.git
cd mmpose
pip install -r requirements.txt
pip install -v -e .

if not exist "dataprep/checkpoints" md "dataprep/checkpoints"
wget https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-l_simcc-coco-wholebody_pt-aic-coco_270e-384x288-eaeb96c8_20230125.pth -outfile dataprep/checkpoints
wget  https://download.openmmlab.com/mmdetection/v2.0/faster_rcnn/faster_rcnn_r50_fpn_1x_coco/faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth -outfile dataprep/checkpoints
