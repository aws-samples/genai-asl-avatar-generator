# check NVCC version
nvcc -V

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# install MMEngine, MMCV and MMDetection using MIM
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
mim install "mmdet>=3.0.0"
pip install git+https://github.com/jin-s13/xtcocoapi


git clone https://github.com/open-mmlab/mmpose.git
# The master branch is version 1.x
cd mmpose
pip install -r requirements.txt
pip install -v -e .
