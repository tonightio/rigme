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
RUN pip install torch-cluster
RUN pip install boto3
RUN pip install Werkzeug
RUN pip install torch-scatter==latest+cu101 torch-sparse==latest+cu101 -f https://pytorch-geometric.com/whl/torch-1.4.0.html

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
RUN sudo apt-get install software-properties-common -y 
RUN sudo add-apt-repository ppa:zeehio/libxp -y
RUN wget ftp.us.debian.org/debian/pool/main/libx/libxp/libxp6_1.0.2-2_amd64.deb
RUN sudo dpkg -i libxp6_1.0.2-2_amd64.deb


# Maya installation
#ADD Autodesk_Maya_2020_ML_Linux_64bit.tgz maya/
COPY Autodesk_Maya_2020_ML_Linux_64bit.tgz maya/
RUN mkdir maya/Autodesk 
RUN tar -xvf maya/Autodesk_Maya_2020_ML_Linux_64bit.tgz -C maya/Autodesk/
RUN sudo alien -vc maya/Autodesk/Packages/Maya2020_64-2020.0-235.x86_64.rpm
RUN sudo dpkg -i maya2020-64_2020.0-236_amd64.deb

RUN pip install Rtree

EXPOSE 80
ENTRYPOINT ["python", "convert_image.py"]