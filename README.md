# RigMe

![demo](https://github.com/tonightio/rigme/blob/master/1_wsvCEezTUxgjRkAzdcTdBw.png)

# Python Version
3.7.2

# Possible libraries needed to install

brew install spatialindex

`pip install google-colab torch torchvision scikit-image trimesh torch-cluster open3d torch_geometric torch_sparse torch_scatter torch_scatter`

pip install google-colab torch torchvision scikit-image trimesh torch-cluster open3d torch_geometric torch_sparse torch_scatter gluoncv pycocotools mxnet tensorboard argparse rtree

rtree:

`pip install Rtree`

For Mac:
sudo pip3 install osmnx


#Github Downloads in specificed paths follow the setup procedure for each github repo, mainly in the image background remove tool and lightweight human pose

./image_background_remove_tool: https://github.com/OPHoperHPO/image-background-remove-tool

./lightweight_human_pose_estimation: https://github.com/Daniil-Osokin/lightweight-human-pose-estimation-3d-demo.pytorch

./pifuhd: https://github.com/facebookresearch/pifuhd

./RigNet_Master: https://github.com/zhan-xu/RigNet


# Usage
First run the flaks application:

python convert_image.py

Then use this command to send a picture to convert into a 3d model:

 curl -X POST http://0.0.0.0:80/api/convert_picture --form file=@./sample_images/test_v4.jpg --form resolution=78

# Setting up Blender

download:

https://www.blender.org/download/

execute:
echo "alias blender=###PATH_TO_BLENDER.APP/Contents/MacOS/blender" >> ~/.bash_profile


#####IMPORTANT CODE########
Xvfb :19 -screen 0 1024x768x16 &
export DISPLAY=:19




