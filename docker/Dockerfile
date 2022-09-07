FROM rasa/rasa:latest-full

# get root permissions to install more packages
USER root

# install tensorflow-gpu
RUN pip install tensorflow-gpu

RUN apt-get install wget -y
RUN apt-get install gnupg -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install keyboard-configuration -y

# Add NVIDIA package repositories
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-repo-ubuntu1804_10.0.130-1_amd64.deb
RUN dpkg -i cuda-repo-ubuntu1804_10.0.130-1_amd64.deb
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
RUN apt-get update

RUN wget http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64/nvidia-machine-learning-repo-ubuntu1804_1.0.0-1_amd64.deb
RUN apt install ./nvidia-machine-learning-repo-ubuntu1804_1.0.0-1_amd64.deb
RUN apt-get update

# Install NVIDIA driver
RUN apt-get install --no-install-recommends -y nvidia-driver-418

# Install TensorRT. Requires that libcudnn7 is installed above.
RUN apt-get install -y --no-install-recommends libnvinfer6=6.0.1-1+cuda10.0 libnvinfer-dev=6.0.1-1+cuda10.0 libnvinfer-plugin6=6.0.1-1+cuda10.0 libnvinfer-plugin-dev=6.0.1-1+cuda10.0

# install python libs
# RUN apt-get install python3-libnvinfer=6.0.1-1+cuda10.0 python3-libnvinfer-dev=6.0.1-1+cuda10.0

# switch bach to 1001
USER 1001
