FROM python:3.7.2
COPY ./convert_image.py /
COPY ./RigNet_master/ /RigNet_master/
COPY ./pifuhd/ /pifuhd/
COPY ./output/ /output/
COPY ./lightweight_human_pose_estimation/ /lightweight_human_pose_estimation/
COPY ./image_background_remove_tool/ /image_background_remove_tool/
WORKDIR /
RUN pip install torch
RUN pip install opencv-python
RUN pip install flask
RUN pip install open3d==0.9
RUN pip install google-colab torchvision scikit-image trimesh torch_geometric gluoncv pycocotools mxnet tensorboard argparse
RUN pip install torch_sparse
RUN pip install torch-cluster
RUN pip install boto3
RUN pip install Werkzeug
RUN pip install torch_scatter

RUN apt-get update\
&& apt-get install curl -y\
&& apt-get install g++ -y\
&& apt-get install make -y\
&& apt-get install sudo -y

RUN sudo apt-get install -y libgl1-mesa-dev

RUN curl -L http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.5.tar.gz | tar xz \
&& cd spatialindex-src-1.8.5\
&& ./configure\
&& make\
&& sudo make install\
&& sudo ldconfig

RUN pip install Rtree
 
# Download and unpack distribution first, Docker's caching
# mechanism will ensure that this only happens once.
RUN wget https://edutrial.autodesk.com/NET18SWDLD/2018/MAYA/ESD/Autodesk_Maya_2018_EN_Linux_64bit.tgz -O maya.tgz && \
    mkdir /maya && tar -xvf maya.tgz -C /maya && \
    rm maya.tgz && \
    rpm -Uvh /maya/Maya*.rpm && \
    rm -r /maya

# Setup environment
ENV MAYA_LOCATION=/usr/autodesk/maya/
ENV PATH=$MAYA_LOCATION/bin:$PATH

# Workaround for "Segmentation fault (core dumped)"
# See https://forums.autodesk.com/t5/maya-general/render-crash-on-linux/m-p/5608552/highlight/true
ENV MAYA_DISABLE_CIP=1

EXPOSE 80
ENTRYPOINT ["python", "convert_image.py"]