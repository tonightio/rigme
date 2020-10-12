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
RUN pip install google-colab torchvision scikit-image trimesh gluoncv pycocotools mxnet tensorboard argparse
RUN pip install torch_sparse
RUN pip install torch-cluster
RUN pip install boto3
RUN pip install Werkzeug
RUN pip install torch_scatter
RUN pip install torch-geometric \
  torch-sparse==latest+cu101 \
  torch-scatter==latest+cu101 \
  torch-cluster==latest+cu101 \
  -f https://pytorch-geometric.com/whl/torch-1.4.0.html

RUN apt-get update\
&& apt-get install curl -y\
&& apt-get install g++ -y\
&& apt-get install make -y\
&& apt-get install sudo -y\
&& apt-get install rpm -y

RUN sudo apt-get install -y libgl1-mesa-dev

RUN curl -L http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.5.tar.gz | tar xz \
&& cd spatialindex-src-1.8.5\
&& ./configure\
&& make\
&& sudo make install\
&& sudo ldconfig

RUN pip install Rtree
 
RUN wget https://up.autodesk.com/2020/MAYA/18BBDBD5-9A15-4095-8D5E-089938EB8E24/Autodesk_Maya_2020_1_ML_Linux_64bit.tgz -O maya.tgz && \
    mkdir /maya && tar -xvf maya.tgz -C /maya && \
    rm maya.tgz && \
    apt-get install alien dpkg-dev debhelper build-essential-y &&\
    alien /maya/Packages/Maya*.rpm && \
    dpkg -i/maya/Packages/Maya*.deb && \
    rm -r /maya

# Setup environment
ENV MAYA_LOCATION=/usr/autodesk/maya/
ENV PATH=$MAYA_LOCATION/bin:$PATH

# Avoid warning about this variable not set, the path is its default value
RUN mkdir /var/tmp/runtime-root && \
    chmod 0700 /var/tmp/runtime-root
ENV XDG_RUNTIME_DIR=/var/tmp/runtime-root

# Workaround for "Segmentation fault (core dumped)"
# See https://forums.autodesk.com/t5/maya-general/render-crash-on-linux/m-p/5608552/highlight/true
ENV MAYA_DISABLE_CIP=1


EXPOSE 80
ENTRYPOINT ["python", "convert_image.py"]