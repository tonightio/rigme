FROM python:3.7.2
COPY ./convert_image.py /
COPY ./RigNet_master/ /RigNet_master/
COPY ./pifuhd/ /pifuhd/
COPY ./output/ /output/
COPY ./lightweight_human_pose_estimation/ /lightweight_human_pose_estimation/
COPY ./image_background_remove_tool/ /image_background_remove_tool/
WORKDIR /
RUN pip install torch==1.6.0
RUN pip install opencv-python
RUN pip install flask
RUN pip install open3d==0.9
RUN pip install google-colab torchvision scikit-image trimesh torch_geometric gluoncv pycocotools mxnet tensorboard argparse
RUN pip install torch-cluster
RUN pip install boto3
RUN pip install Werkzeug
RUN pip install torch-scatter==2.0.5+cu101 torch-sparse==0.6.7+cu101 -f https://pytorch-geometric.com/whl/torch-1.6.0.html

RUN apt-get update\
&& apt-get install curl -y\
&& apt-get install g++ -y\
&& apt-get install make -y\
&& apt-get install sudo -y

RUN sudo apt-get install -y libgl1-mesa-dev
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN echo exit 0 > /usr/sbin/policy-rc.d

RUN curl -L http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.5.tar.gz | tar xz \
&& cd spatialindex-src-1.8.5\
&& ./configure\
&& make\
&& sudo make install\
&& sudo ldconfig \
&& sudo apt-get install dialog apt-utils -y

RUN sudo apt-get install alien dpkg-dev debhelper build-essential zlib1g-dev -y
RUN sudo apt-get update


# Maya installation
COPY Autodesk_Maya_2020_ML_Linux_64bit.tgz maya/
RUN mkdir maya/Autodesk 
RUN tar -xvf maya/Autodesk_Maya_2020_ML_Linux_64bit.tgz -C maya/Autodesk/
RUN sudo alien -vc maya/Autodesk/Packages/Maya2020_64-2020.0-235.x86_64.rpm
RUN sudo dpkg -i maya2020-64_2020.0-236_amd64.deb

# Setup environment
ENV MAYA_LOCATION=/usr/autodesk/maya/
ENV MAYAPYPATH=$MAYA_LOCATION/bin:$PATH

# Avoid warning about this variable not set, the path is its default value
RUN mkdir /var/tmp/runtime-root && \
    chmod 0700 /var/tmp/runtime-root
ENV XDG_RUNTIME_DIR=/var/tmp/runtime-root

# Workaround for "Segmentation fault (core dumped)"
# See https://forums.autodesk.com/t5/maya-general/render-crash-on-linux/m-p/5608552/highlight/true
ENV MAYA_DISABLE_CIP=1

RUN pip install Rtree

EXPOSE 80
ENTRYPOINT ["python", "convert_image.py"]
