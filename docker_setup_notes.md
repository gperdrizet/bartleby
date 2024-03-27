# Docker containerization notes

## 1. Docker

Start with a fresh, up-to-date docker install if needed. From the [Ubuntu install instructions](https://docs.docker.com/engine/install/ubuntu/)

Remove old install

```text
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
sudo apt-get purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
```

Then install Docker from the Docker apt repository:

```text
sudo apt update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify the install with:

```text
$ sudo docker run hello-world

Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
c1ec31eb5944: Pull complete 
Digest: sha256:d000bc569937abbe195e20322a0bde6b2922d805332fd6d8a68b19f524b7d21d
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.
```

OK! Looks good. Now, make a docker user group and add yourself.

```text
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

Set Docker to run on boot:

```text
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

Finally, set up log rotation. Add the following to */etc/docker/daemon.json*, creating the file if it doesn't exist.

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Then restart the daemon:

```text
sudo systemctl restart docker
```

## 2. Nvidia container toolkit

To run Nvidia/CUDA containers we need the Nvidia container toolkit. First add the repo:

```text
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

Then update and install the toolkit:

```text
sudo apt update
sudo apt install nvidia-container-toolkit
```

Now, configure docker and restart the daemon:

```text
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

This will make changes to */etc/docker/daemon.json*:

```json
{
    "log-driver": "json-file",
    "log-opts": {
        "max-file": "3",
        "max-size": "10m"
    },
    "runtimes": {
        "nvidia": {
            "args": [],
            "path": "nvidia-container-runtime"
        }
    }
}
```

Test with:

```text
$ sudo docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi

Unable to find image 'ubuntu:latest' locally
latest: Pulling from library/ubuntu
bccd10f490ab: Pull complete 
Digest: sha256:77906da86b60585ce12215807090eb327e7386c8fafb5402369e421f44eff17e
Status: Downloaded newer image for ubuntu:latest
Tue Mar 12 21:50:44 2024       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 470.42.01    Driver Version: 470.42.01    CUDA Version: 11.4     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  Tesla K80           On   | 00000000:05:00.0 Off |                    0 |
| N/A   28C    P8    26W / 149W |      0MiB / 11441MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+
|   1  Tesla K80           On   | 00000000:06:00.0 Off |                    0 |
| N/A   33C    P8    29W / 149W |      0MiB / 11441MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```

OK, looks good.

## 2. Containerize

Initialize the docker assets using VSCode command *Docker: Add Docker Files to Workspace*.

Updated Dockerfile:

```text
# For more information, please refer to https://aka.ms/vscode-docker-python
#FROM nvidia/cuda:11.3.1-runtime-ubuntu20.04
FROM nvidia/cuda:11.4.3-base-ubuntu20.04

# Keep apt-get from interactively asking for a timezone
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="America/New_York"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set location of Google service account credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/bartleby/bartleby/credentials/service_key.json"

# Install python 3.8 & pip
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

# Move the bartleby source code in
WORKDIR /bartleby
COPY . /bartleby

# Set-up CUDA and the CUDA toolkit
RUN apt-get install -y wget
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
RUN mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
RUN wget https://developer.download.nvidia.com/compute/cuda/11.4.0/local_installers/cuda-repo-ubuntu2004-11-4-local_11.4.0-470.42.01-1_amd64.deb
RUN dpkg -i cuda-repo-ubuntu2004-11-4-local_11.4.0-470.42.01-1_amd64.deb
RUN apt-key add /var/cuda-repo-ubuntu2004-11-4-local/7fa2af80.pub
RUN apt-get update -y
RUN apt-get install -y cuda
RUN apt-get install -y nvidia-cuda-toolkit

# Set path to correct CUDA version
ENV export PATH=/usr/local/cuda-11.4/bin${PATH:+:${PATH}}

# Build and install bitsandbytes
WORKDIR /bartleby/bitsandbytes
RUN CUDA_VERSION=118 make cuda11x_nomatmul_kepler
RUN python3 setup.py install

# Install pip requirements
WORKDIR /bartleby
RUN python3 -m pip install -r requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" bartleby && chown -R bartleby /bartleby
USER bartleby

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python3", "-m", "bartleby"]
```

Added the following to .dockerignore:

```text
LICENSE
README.md
NOTES.md
architecture.md
docker_setup_notes.md
bartleby/hf_cache
bartleby/logs
```

Freeze the venv:

```text
python -m pip freeze > requirements.txt
```

Build the image and start the container:

```text
docker build -t bartleby .
docker run --gpus all --name bartleby -d bartleby:latest
```

OK, having issues with CUDA, CUDA toolkit version and bitsandbytes. Maybe we don't need to install the CUDA toolkit and build bitsandbytes in the container. Let's take a look and the Nvidia container images and see how they differ.

### 3. Nvidia images

#### nvidia/cuda:11.4.3-base-ubuntu20.04

```text
$ nvidia-smi

Sat Mar 23 01:13:37 2024       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 470.42.01    Driver Version: 470.42.01    CUDA Version: 11.4     |
|-------------------------------+----------------------+----------------------+
```

```text
$ nvcc --version

bash: nvcc: command not found
```

#### nvidia/cuda:11.4.3-runtime-ubuntu20.04

```text
$ nvidia-smi

Sat Mar 23 01:26:02 2024       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 470.42.01    Driver Version: 470.42.01    CUDA Version: 11.4     |
|-------------------------------+----------------------+----------------------+
```

```text
$ nvcc --version

bash: nvcc: command not found
```

#### nvidia/cuda:11.4.3-devel-ubuntu20.04

```text
$ nvidia-smi

Sat Mar 23 01:34:07 2024       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 470.42.01    Driver Version: 470.42.01    CUDA Version: 11.4     |
|-------------------------------+----------------------+----------------------+
```

```text
$ nvcc --version

nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2021 NVIDIA Corporation
Built on Mon_Oct_11_21:27:02_PDT_2021
Cuda compilation tools, release 11.4, V11.4.152
Build cuda_11.4.r11.4/compiler.30521435_0
```

#### nvidia/cuda:11.4.3-cudnn8-runtime-ubuntu20.04

```text
$ nvidia-smi

Sat Mar 23 01:38:45 2024       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 470.42.01    Driver Version: 470.42.01    CUDA Version: 11.4     |
|-------------------------------+----------------------+----------------------+
```

```text
$ nvcc --version

bash: nvcc: command not found
```

OK, what have we learned - still not really sure exactly what the difference between the base and runtime images are, but the devel image looks just like my host system install from inside the container. Nvidia-smi reports 470 driver and CUDA 11.4 and nvcc reports 11.4/11.4. However, although, building and installing bitsandbytes from the Dockerfile appears to work, running the bitsandbytes test inside the container fails with what looks like a bunch of path issues. Coulden't figure it out. Let's try building and installing from inside the running container.

### 4. CUDA+bitsandbytes troubleshooting

#### 4.1. Install bitsandbytes manualy inside running container

Let's first try installing from a copy of the host system's bitsandbytes directory:

```text
python3 setup.py install
```

Seems to work, no errors. Now check it:

```text
$ python3 -m bitsandbytes

Traceback (most recent call last):
  File "/usr/lib/python3.8/runpy.py", line 185, in _run_module_as_main
    mod_name, mod_spec, code = _get_module_details(mod_name, _Error)
  File "/usr/lib/python3.8/runpy.py", line 144, in _get_module_details
    return _get_module_details(pkg_main_name, error)
  File "/usr/lib/python3.8/runpy.py", line 111, in _get_module_details
    __import__(pkg_name)
  File "/bartleby/bitsandbytes/bitsandbytes/__init__.py", line 6, in <module>
    from . import cuda_setup, utils, research
  File "/bartleby/bitsandbytes/bitsandbytes/utils.py", line 4, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
```

OK, install torch. Same version as in the requirements.txt from the host venv.

```text
pip install torch==1.13.1
```

Seems to go well, test bitsandbytes again - this time we need scipy:

```text
pip install scipy==1.10.1
```

And test again:

```text
$ python3 -m bitsandbytes

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ BUG REPORT INFORMATION ++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

++++++++++++++++++ /usr/local CUDA PATHS +++++++++++++++++++
/usr/local/lib/python3.8/dist-packages/torch/lib/libtorch_cuda.so
/usr/local/lib/python3.8/dist-packages/torch/lib/libc10_cuda.so
/usr/local/lib/python3.8/dist-packages/torch/lib/libtorch_cuda_cpp.so
/usr/local/lib/python3.8/dist-packages/torch/lib/libtorch_cuda_linalg.so
/usr/local/lib/python3.8/dist-packages/torch/lib/libtorch_cuda_cu.so
/usr/local/cuda-11.4/targets/x86_64-linux/lib/stubs/libcuda.so
/usr/local/cuda-11.4/targets/x86_64-linux/lib/libcudart.so
/usr/local/cuda-11.4/compat/libcuda.so

+++++++++++++++ WORKING DIRECTORY CUDA PATHS +++++++++++++++
/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda114.so
/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda117.so
/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda118.so
/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda114_nocublaslt.so
/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so
/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda114.so
/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda117.so
/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda118.so
/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda114_nocublaslt.so
/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so

++++++++++++++++++ LD_LIBRARY CUDA PATHS +++++++++++++++++++

++++++++++++++++++++++++++ OTHER +++++++++++++++++++++++++++
COMPILED_WITH_CUDA = True
COMPUTE_CAPABILITIES_PER_GPU = ['6.1', '3.7', '3.7']
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++ DEBUG INFO END ++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Running a quick check that:
    + library is importable
    + CUDA function is callable


WARNING: Please be sure to sanitize sensible info from any such env vars!

SUCCESS!
Installation was successful!
```

#### 4.2. Install bitsandbytes from Dockerfile

Cool! Worked - no idea if it will actually import and run, but let's try reproducing that result from our Dockerfile:

```text
FROM nvidia/cuda:11.4.3-devel-ubuntu20.04

WORKDIR /

# Install python 3.8 & pip
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

# Install some bitsandbytes prerequisites
pip install scipy==1.10.1
pip install torch==1.13.1

# Move the bartleby and bitsandbytes source code in
WORKDIR /bartleby
COPY . /bartleby

# Build install bitsandbytes
WORKDIR /bartleby/bitsandbytes
RUN python3 setup.py install

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" bartleby && chown -R bartleby /bartleby
USER bartleby

# Test bitsandbytes
CMD ["python3", "-m", "bitsandbytes"]

```

Note: the torch install pulls in the cuda runtime and cudnn for cuda 11. We may not actually have to use the full devel container. If this works, let's try it in base.

OK, cool - it worked. Let's try base first. Same dockerfile just using nvidia/cuda:11.4.3-base-ubuntu20.04. didn't work, let's try nvidia/cuda:11.4.3-runtime-ubuntu20.04. Nice - runtime worked. Now, let's move on and run the whole thing end-to-end. Here's the dockerfile:

```text
FROM nvidia/cuda:11.4.3-runtime-ubuntu20.04

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set location of Google service account credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/bartleby/bartleby/credentials/service_key.json"

WORKDIR /

# Install python 3.8 & pip
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

# Install some bitsandbytes prerequisites
RUN pip install scipy==1.10.1
RUN pip install torch==1.13.1

# Move the bartleby and bitsandbytes source code in
WORKDIR /bartleby
COPY . /bartleby

# Build install bitsandbytes
WORKDIR /bartleby/bitsandbytes
RUN python3 setup.py install

# Install pip requirements
WORKDIR /bartleby
RUN python3 -m pip install -r requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" bartleby && chown -R bartleby /bartleby
USER bartleby

# Test bitsandbytes
CMD ["python3", "-m", "bartleby"]
```

And, here is requirements.txt. We commented out scipy, torch, bitsandbytes and all of the nvidia stuff because we install them manually earlier in the build.

```text
absl-py==2.1.0
accelerate==0.26.1
aiofiles==23.2.1
aiohttp==3.9.3
aiohttp-socks==0.8.4
aiosignal==1.3.1
async-timeout==4.0.3
attrs==23.2.0
# bitsandbytes==0.41.2 Need to install bnb via setup.py inside container to get version built with target cuda11x_nomatmul_kepler
cachetools==5.3.2
certifi==2024.2.2
charset-normalizer==3.3.2
click==8.1.7
cmake==3.28.3
datasets==2.18.0
dill==0.3.8
discord.py==2.3.2
evaluate==0.4.1
filelock==3.13.1
frozenlist==1.4.1
fsspec==2024.2.0
git-filter-repo==2.38.0
google-api-core==2.17.0
google-api-python-client==2.116.0
google-auth==2.27.0
google-auth-httplib2==0.2.0
googleapis-common-protos==1.62.0
h11==0.14.0
h2==4.1.0
hpack==4.0.0
httplib2==0.22.0
huggingface-hub==0.20.3
hyperframe==6.0.1
idna==3.6
importlib-resources==6.1.1
Jinja2==3.1.3
joblib==1.3.2
jsonschema==4.21.1
jsonschema-specifications==2023.12.1
lit==17.0.6
lxml==5.1.0
MarkupSafe==2.1.5
matrix-nio==0.24.0
mpmath==1.3.0
multidict==6.0.5
multiprocess==0.70.16
networkx==3.1
nltk==3.8.1
numpy==1.24.4
#nvidia-cublas-cu11==11.10.3.66
#nvidia-cublas-cu12==12.1.3.1
#nvidia-cuda-cupti-cu11==11.7.101
#nvidia-cuda-cupti-cu12==12.1.105
#nvidia-cuda-nvrtc-cu11==11.7.99
#nvidia-cuda-nvrtc-cu12==12.1.105
#nvidia-cuda-runtime-cu11==11.7.99
#nvidia-cuda-runtime-cu12==12.1.105
#nvidia-cudnn-cu11==8.5.0.96
#nvidia-cudnn-cu12==8.9.2.26
#nvidia-cufft-cu11==10.9.0.58
#nvidia-cufft-cu12==11.0.2.54
#nvidia-curand-cu11==10.2.10.91
#nvidia-curand-cu12==10.3.2.106
#nvidia-cusolver-cu11==11.4.0.1
#nvidia-cusolver-cu12==11.4.5.107
#nvidia-cusparse-cu11==11.7.4.91
#nvidia-cusparse-cu12==12.1.0.106
#nvidia-nccl-cu11==2.14.3
#nvidia-nccl-cu12==2.19.3
#nvidia-nvjitlink-cu12==12.3.101
#nvidia-nvtx-cu11==11.7.91
#nvidia-nvtx-cu12==12.1.105
packaging==23.2
pandas==2.0.3
pillow==10.2.0
pkgutil-resolve-name==1.3.10
protobuf==4.25.2
psutil==5.9.8
pyarrow==15.0.0
pyarrow-hotfix==0.6
pyasn1==0.5.1
pyasn1-modules==0.3.0
pycryptodome==3.20.0
pyparsing==3.1.1
python-dateutil==2.8.2
python-docx==1.1.0
python-socks==2.4.4
pytz==2024.1
PyYAML==6.0.1
referencing==0.33.0
regex==2023.12.25
requests==2.31.0
responses==0.18.0
rouge-score==0.1.2
rpds-py==0.17.1
rsa==4.9
safepickle==0.2.0
safetensors==0.4.2
#scipy==1.10.1
sentencepiece==0.2.0
six==1.16.0
sympy==1.12
tokenizers==0.15.1
#torch==1.13.1
#torchaudio==0.13.1
#torchvision==0.14.1
tqdm==4.66.1
transformers==4.37.2
triton==2.0.0
typing-extensions==4.9.0
tzdata==2024.1
unpaddedbase64==2.1.0
uritemplate==4.1.1
urllib3==2.2.0
xxhash==3.4.1
yarl==1.9.4
zipp==3.17.0

```

OK, didn't work - either something we added to the dockerfile changed how things are being installed or something we installed via requirements broke our cuda install.

Here is the plan for tomorrow. I think we should try and make a fresh, minimal and uncluttered env. My bet is something is pulling a dependency or something that breaks cuda. This might not have been a problem in the host system due to the order of operations? I dunno - somewhat grasping at straws here. So, let's put the production version of bartleby in a docker container running on CPU only, then if someone tries it, at least it works. Then we can have more freedom to screw around on the host system and figure out how to reliably install everything we need to get up and running.

### 5. Temporary backup plan: CPU only container

Here is the setup for a CPU only image:

1. Uncomment everything in requirements except bitsandbytes
2. Comment out the individual installs of torch and scipy
3. Edit config and set quantization to none and device map to cpu

OK - Here is what we actually need to run (at least on discord). Note: it's around half the size of the main venv:

```text
accelerate==0.26.1
aiofiles==23.2.1
aiohttp==3.9.3
aiohttp-socks==0.8.4
aiosignal==1.3.1
async-timeout==4.0.3
attrs==23.2.0
bitsandbytes==0.41.2
cachetools==5.3.3
certifi==2024.2.2
charset-normalizer==3.3.2
discord.py==2.3.2
filelock==3.13.1
frozenlist==1.4.1
fsspec==2024.3.1
google-api-core==2.17.0
google-api-python-client==2.116.0
google-auth==2.29.0
google-auth-httplib2==0.2.0
googleapis-common-protos==1.63.0
h11==0.14.0
h2==4.1.0
hpack==4.0.0
httplib2==0.22.0
huggingface-hub==0.21.4
hyperframe==6.0.1
idna==3.6
importlib-resources==6.4.0
jsonschema==4.21.1
jsonschema-specifications==2023.12.1
lxml==5.1.0
matrix-nio==0.24.0
multidict==6.0.5
numpy==1.24.4
nvidia-cublas-cu11==11.10.3.66
nvidia-cuda-nvrtc-cu11==11.7.99
nvidia-cuda-runtime-cu11==11.7.99
nvidia-cudnn-cu11==8.5.0.96
packaging==24.0
pkgutil-resolve-name==1.3.10
protobuf==4.25.3
psutil==5.9.8
pyasn1==0.5.1
pyasn1-modules==0.3.0
pycryptodome==3.20.0
pyparsing==3.1.2
python-docx==1.1.0
python-socks==2.4.4
PyYAML==6.0.1
referencing==0.34.0
regex==2023.12.25
requests==2.31.0
rpds-py==0.18.0
rsa==4.9
safetensors==0.4.2
scipy==1.10.1
sentencepiece==0.2.0
tokenizers==0.15.2
torch==1.13.1
tqdm==4.66.2
transformers==4.37.2
typing-extensions==4.10.0
unpaddedbase64==2.1.0
uritemplate==4.1.1
urllib3==2.2.1
yarl==1.9.4
zipp==3.18.1

```

OK, now the dockerfile:

```text
FROM nvidia/cuda:11.4.3-runtime-ubuntu20.04

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set location of Google service account credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/bartleby/bartleby/credentials/service_key.json"

WORKDIR /

# Install python 3.8 & pip
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

# Move the bartleby and bitsandbytes source code in
WORKDIR /bartleby
COPY . /bartleby

# Build install bitsandbytes
# WORKDIR /bartleby/bitsandbytes
# RUN python3 setup.py install

# Install pip requirements
WORKDIR /bartleby
RUN python3 -m pip install -r requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" bartleby && chown -R bartleby /bartleby
USER bartleby

# Test bitsandbytes
CMD ["python3", "-m", "bartleby"]
```

Thought for sure we had it that time, but no. Still have some sort of path issues going on inside the container. Heres the log:

```text
False

===================================BUG REPORT===================================
================================================================================
The following directories listed in your path were found to be non-existent: {PosixPath('/usr/local/nvidia/lib'), PosixPath('/usr/local/nvidia/lib64')}
/usr/local/lib/python3.8/dist-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/cuda_setup/main.py:166: UserWarning: Welcome to bitsandbytes. For bug reports, please run

python -m bitsandbytes


/usr/local/lib/python3.8/dist-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/cuda_setup/main.py:166: UserWarning: /usr/local/nvidia/lib:/usr/local/nvidia/lib64 did not contain ['libcudart.so', 'libcudart.so.11.0', 'libcudart.so.12.0'] as expected! Searching further paths...
/usr/local/lib/python3.8/dist-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/cuda_setup/main.py:166: UserWarning: WARNING: Compute capability < 7.5 detected! Only slow 8-bit matmul is supported for your GPU!                     If you run into issues with 8-bit matmul, you can try 4-bit quantization: https://huggingface.co/blog/4bit-transformers-bitsandbytes
CUDA_SETUP: WARNING! libcudart.so not found in any environmental path. Searching in backup paths...
DEBUG: Possible options found for libcudart.so: {PosixPath('/usr/local/cuda/lib64/libcudart.so.11.0')}
CUDA SETUP: PyTorch settings found: CUDA_VERSION=117, Highest Compute Capability: 3.7.
CUDA SETUP: To manually override the PyTorch CUDA version please see:https://github.com/TimDettmers/bitsandbytes/blob/main/how_to_use_nonpytorch_cuda.md
CUDA SETUP: Required library version not found: libbitsandbytes_cuda117_nocublaslt.so. Maybe you need to compile it from source?
CUDA SETUP: Defaulting to libbitsandbytes_cpu.so...

================================================ERROR=====================================
CUDA SETUP: CUDA detection failed! Possible reasons:
1. You need to manually override the PyTorch CUDA version. Please see: "https://github.com/TimDettmers/bitsandbytes/blob/main/how_to_use_nonpytorch_cuda.md
2. CUDA driver not installed
3. CUDA not installed
4. You have multiple conflicting CUDA libraries
5. Required library not pre-compiled for this bitsandbytes release!
CUDA SETUP: If you compiled from source, try again with `make CUDA_VERSION=DETECTED_CUDA_VERSION` for example, `make CUDA_VERSION=113`.
CUDA SETUP: The CUDA version for the compile might depend on your conda install. Inspect CUDA version via `conda list | grep cuda`.
================================================================================

CUDA SETUP: Something unexpected happened. Please compile from source:
git clone https://github.com/TimDettmers/bitsandbytes.git
cd bitsandbytes
CUDA_VERSION=117 make cuda11x_nomatmul
python setup.py install
CUDA SETUP: Setup Failed!
```

### 6. Bitsandbytes+CUDA troubleshooting: install from inside container (again)

Plan now is to try starting with a 'nude' container, i.e. updated nvidia/cuda:11.4.3-runtime-ubuntu20.04 with just python & pip installed. Then do the set-up manually from inside the container and see what, if anything goes wrong. Here is the dockerfile:

```text
FROM nvidia/cuda:11.4.3-runtime-ubuntu20.04

WORKDIR /

# Install python 3.8 & pip
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

# Move the bartleby and bitsandbytes source code in
WORKDIR /bartleby
COPY . /bartleby

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" bartleby && chown -R bartleby /bartleby
USER bartleby
```

#### Manual container install notes

Right off the bat, I am seeing warnings. During the pip torch install the following appears:

```text
  WARNING: The script isympy is installed in '/home/bartleby/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
  WARNING: The scripts convert-caffe2-to-onnx, convert-onnx-to-caffe2 and torchrun are installed in '/home/bartleby/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
```

Install appears to complete successfully.

Also, seeing similar warnings during the transformers install:

```text
  WARNING: The script tqdm is installed in '/home/bartleby/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
  WARNING: The scripts f2py, f2py3 and f2py3.8 are installed in '/home/bartleby/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
  WARNING: The script normalizer is installed in '/home/bartleby/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
  WARNING: The script huggingface-cli is installed in '/home/bartleby/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
  WARNING: The script transformers-cli is installed in '/home/bartleby/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
```

These are all related to the 'bartleby' user's home directory. I wonder if we even need that? I think it was added by vscode when we generated the docker assets. Let's try removing that from the dockerfile and starting again.

OK, cool. No warnings this time. Proceeding with manual environment setup. Except this (which was expected).

```text
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behavior with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
```

Sweet, it works! Let's add everything back to the dockerfile, except the adduser stuff and try building the image again.

### 7. Bitsandbytes+CUDA troubleshooting: install from Dockerfile (again)

Holy crap, this is frustrating. Still doesn't work via the dockerfile. I really don't understand why. My only thought it that installing via requirements doesn't work and it's not docker's problem. It is true that I have never tested just cloning the repo fresh and setting it up with pip. I think, for now, to avoid going down that rabbit hole and to just get the container working, I am going to add the exact commands in the exact order it takes to get a clean venv working into the dockerfile.

```text
FROM nvidia/cuda:11.4.3-runtime-ubuntu20.04

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set location of Google service account credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/bartleby/bartleby/credentials/service_key.json"

WORKDIR /

# Install python 3.8 & pip
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

# Move the bartleby and bitsandbytes source code in
WORKDIR /bartleby
COPY . /bartleby

# Install dependencies
WORKDIR /bartleby
RUN pip install torch==1.13.1
RUN pip install transformers==4.37.2
RUN pip install discord.py==2.3.2
RUN pip install matrix-nio==0.24.0
RUN pip install google-api-core==2.17.0
RUN pip install python-docx==1.1.0
RUN pip install google-api-python-client==2.116.0
RUN pip install sentencepiece==0.2.0
RUN pip install accelerate==0.26.1
RUN pip install scipy==1.10.1

# Install bitsandbytes
WORKDIR /bartleby/bitsandbytes
RUN python3 setup.py install

# Run bartleby
WORKDIR /bartleby
CMD ["python3", "-m", "bartleby"]
```

### 7. Clean-up and finalize

FINALLY works. Going to do a few more things:

1. Move the docker data dir to arkk
2. Make a clean venv for the project
3. Load secrets via environment variables from the venv
4. Build a GPU production image
5. Push it to a public repo on dockerhub
6. Run it locally for the live discord instance

#### 7.1. Secrets

Google Cloud is the tricky one - you can either provide the path to a credential file via an environment variable, but I don't want to put the credential file inside of the container. So, for now instead of setting up workload identity federation (whatever that is) the plan is to bind mount bartleby's host machine credentials folder into the container. Then folks who want to do the same can put their own credentials there and we should be good to go. This also doesn't require any changes to bartleby's code itself, just the way we run the container.

Here are the setup instructions:

1. Add the host machine's credentials directory to .dockerignore
2. Make an empty credentials directory inside the container via the Dockerfile
3. Set the Google application credentials environment var via the Dockerfile
4. Bind mount the host machine's credentials directory onto the container's at runtime:

```text
docker run --gpus all --mount type=bind,source="$(pwd)"/bartleby/credentials,target=/bartleby/bartleby/credentials --name bartleby -d bartleby:latest
```

OK, cool works great.

#### 7.2. Data location

Add the data-root parameter with the new target to */etc/docker/daemon.json' on the host machine:

```json
{
    "data-root": "/mnt/arkk/docker",
    "log-driver": "json-file",
    "log-opts": {
        "max-file": "3",
        "max-size": "10m"
    },
    "runtimes": {
        "nvidia": {
            "args": [],
            "path": "nvidia-container-runtime"
        }
    }
}
```

And restart docker:

```text
sudo systemctl docker restart
```

### 8. 2024-03-26: More problems

OK, so we are back here again:

```text
False

===================================BUG REPORT===================================
/usr/local/lib/python3.8/dist-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/cuda_setup/main.py:166: UserWarning: Welcome to bitsandbytes. For bug reports, please run

python -m bitsandbytes

================================================================================
The following directories listed in your path were found to be non-existent: {PosixPath('/usr/local/nvidia/lib64'), PosixPath('/usr/local/nvidia/lib')}
The following directories listed in your path were found to be non-existent: {PosixPath('PATH=/usr/local/nvidia/bin'), PosixPath('/usr/local/cuda-11.4/bin'), PosixPath('/usr/local/cuda/bin')}
CUDA_SETUP: WARNING! libcudart.so not found in any environmental path. Searching in backup paths...
DEBUG: Possible options found for libcudart.so: {PosixPath('/usr/local/cuda/lib64/libcudart.so.11.0')}
CUDA SETUP: PyTorch settings found: CUDA_VERSION=117, Highest Compute Capability: 3.7.
CUDA SETUP: To manually override the PyTorch CUDA version please see:https://github.com/TimDettmers/bitsandbytes/blob/main/how_to_use_nonpytorch_cuda.md

  warn(msg)
CUDA SETUP: Required library version not found: libbitsandbytes_cuda117_nocublaslt.so. Maybe you need to compile it from source?
CUDA SETUP: Defaulting to libbitsandbytes_cpu.so...

================================================ERROR=====================================
CUDA SETUP: CUDA detection failed! Possible reasons:
1. You need to manually override the PyTorch CUDA version. Please see: "https://github.com/TimDettmers/bitsandbytes/blob/main/how_to_use_nonpytorch_cuda.md
2. CUDA driver not installed
3. CUDA not installed
4. You have multiple conflicting CUDA libraries
/usr/local/lib/python3.8/dist-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/cuda_setup/main.py:166: UserWarning: /usr/local/nvidia/lib:/usr/local/nvidia/lib64 did not contain ['libcudart.so', 'libcudart.so.11.0', 'libcudart.so.12.0'] as expected! Searching further paths...
  warn(msg)
5. Required library not pre-compiled for this bitsandbytes release!
/usr/local/lib/python3.8/dist-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/cuda_setup/main.py:166: UserWarning: WARNING: Compute capability < 7.5 detected! Only slow 8-bit matmul is supported for your GPU!                     If you run into issues with 8-bit matmul, you can try 4-bit quantization: https://huggingface.co/blog/4bit-transformers-bitsandbytes
  warn(msg)
CUDA SETUP: If you compiled from source, try again with `make CUDA_VERSION=DETECTED_CUDA_VERSION` for example, `make CUDA_VERSION=113`.
CUDA SETUP: The CUDA version for the compile might depend on your conda install. Inspect CUDA version via `conda list | grep cuda`.
================================================================================

CUDA SETUP: Something unexpected happened. Please compile from source:
git clone https://github.com/TimDettmers/bitsandbytes.git
cd bitsandbytes
CUDA_VERSION=117 make cuda11x_nomatmul
python setup.py install
CUDA SETUP: Setup Failed!
```

Only real changes to my knowledge were:

1. Rebuilding fresh host system venv (following the dependency pins used in the container)
2. Adding Jinja2==3.1.3

Had a moment where I thought that the problem was due to using the GTX1070 vs K80s, but that does not seem to be the case. Also, works fine from the host system.

1. Last time we were stuck in a 'works fine from the host system' situation, we manualy rebuilt a working minimal venv and then used explicitly used the versions of those dependencies selected by pip in the docker file. We should try that again.
2. Maybe something changed and we need to rebuild bitsandbytes?
3. We should probably have a local copy of the base image incase something changes upstream.
4. It would also be cool to have a CUDA/torch/transformers/bitsandbytes image to fall back on.

#### Fresh test venv

Right off the bat, installing pip installing torch on the host system (which has 470 driver CUDA 11.4/11.4) pulls the wrong version and puts the wrong CUDA stuff in the venv. Let's do a little work to document how and why I know what torch version to use.

#### PyTorch version

Seems like 1.13.1 is the correct version - this is the only version that exists in the working host machine venv. Looking on the [PyTorch website](https://pytorch.org/get-started/previous-versions/) it seems like it only supports CUDA 11.7 and 11.8, but I believe we did a trial and error version regression to determine the most recent version which would work the first time we got all of this figured out. The instructions say to install it like this:

```text
# CUDA 11.7
pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu117
```

But we don't need vision and audio, also I am worried that explicitly installing pytorch-cuda 11.7 will break things. Let's try it this way and see what happened:

```text
pip install torch==1.13.1
```

OK, we get torch 1.13.1 and a couple of Nvidia CUDA cuDNN things all versions 11.7 or 11.10. Now let's just iteratively try and run bartleby and then install whatever it complains about. Version number after the comment is what pip chose.

```text
pip install transformers #4.39.1
pip install discord.py #2.3.2
pip install matrix-nio #0.24.0
pip install google-api-core #2.18.0
pip install python-docx #1.1.0
pip install google-api-python-client #2.123.0
```

At this point, need to set:

```text
export GOOGLE_APPLICATION_CREDENTIALS="bartleby/credentials/service_key.json"
```

to keep running bartleby. More installs:

```text
pip install SentencePiece #0.2.0
pip install accelerate #0.28.0
```

OK, at this point, we are getting a 'importlib.metadata.PackageNotFoundError: bitsandbytes' error from the discord logger inside of bartleby. Let's try just installing it via setup.py in the venv, rather than rebuilding.

```text
(test-venv)$ cd bitsandbytes
(test-venv)$ python setup.py install
(test-venv)$ python -m bitsandbytes

False

===================================BUG REPORT===================================
/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/cuda_setup/main.py:166: UserWarning: Welcome to bitsandbytes. For bug reports, please run

python -m bitsandbytes


  warn(msg)
================================================================================
CUDA_SETUP: WARNING! libcudart.so not found in any environmental path. Searching in backup paths...
/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/cuda_setup/main.py:166: UserWarning: Found duplicate ['libcudart.so', 'libcudart.so.11.0', 'libcudart.so.12.0'] files: {PosixPath('/usr/local/cuda/lib64/libcudart.so.11.0'), PosixPath('/usr/local/cuda/lib64/libcudart.so')}.. We select the PyTorch default libcudart.so, which is {torch.version.cuda},but this might missmatch with the CUDA version that is needed for bitsandbytes.To override this behavior set the BNB_CUDA_VERSION=<version string, e.g. 122> environmental variableFor example, if you want to use the CUDA version 122BNB_CUDA_VERSION=122 python ...OR set the environmental variable in your .bashrc: export BNB_CUDA_VERSION=122In the case of a manual override, make sure you set the LD_LIBRARY_PATH, e.g.export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-11.2
  warn(msg)
DEBUG: Possible options found for libcudart.so: {PosixPath('/usr/local/cuda/lib64/libcudart.so.11.0'), PosixPath('/usr/local/cuda/lib64/libcudart.so')}
CUDA SETUP: PyTorch settings found: CUDA_VERSION=117, Highest Compute Capability: 6.1.
CUDA SETUP: To manually override the PyTorch CUDA version please see:https://github.com/TimDettmers/bitsandbytes/blob/main/how_to_use_nonpytorch_cuda.md
/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/cuda_setup/main.py:166: UserWarning: WARNING: Compute capability < 7.5 detected! Only slow 8-bit matmul is supported for your GPU!                     If you run into issues with 8-bit matmul, you can try 4-bit quantization: https://huggingface.co/blog/4bit-transformers-bitsandbytes
  warn(msg)
CUDA SETUP: Required library version not found: libbitsandbytes_cuda117_nocublaslt.so. Maybe you need to compile it from source?
CUDA SETUP: Defaulting to libbitsandbytes_cpu.so...

================================================ERROR=====================================
CUDA SETUP: CUDA detection failed! Possible reasons:
1. You need to manually override the PyTorch CUDA version. Please see: "https://github.com/TimDettmers/bitsandbytes/blob/main/how_to_use_nonpytorch_cuda.md
2. CUDA driver not installed
3. CUDA not installed
4. You have multiple conflicting CUDA libraries
5. Required library not pre-compiled for this bitsandbytes release!
CUDA SETUP: If you compiled from source, try again with `make CUDA_VERSION=DETECTED_CUDA_VERSION` for example, `make CUDA_VERSION=113`.
CUDA SETUP: The CUDA version for the compile might depend on your conda install. Inspect CUDA version via `conda list | grep cuda`.
================================================================================

CUDA SETUP: Something unexpected happened. Please compile from source:
git clone https://github.com/TimDettmers/bitsandbytes.git
cd bitsandbytes
CUDA_VERSION=117 make cuda11x_nomatmul
python setup.py install
CUDA SETUP: Setup Failed!
Traceback (most recent call last):
  File "/usr/lib/python3.8/runpy.py", line 185, in _run_module_as_main
    mod_name, mod_spec, code = _get_module_details(mod_name, _Error)
  File "/usr/lib/python3.8/runpy.py", line 144, in _get_module_details
    return _get_module_details(pkg_main_name, error)
  File "/usr/lib/python3.8/runpy.py", line 111, in _get_module_details
    __import__(pkg_name)
  File "/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/__init__.py", line 6, in <module>
    from . import cuda_setup, utils, research
  File "/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/research/__init__.py", line 1, in <module>
    from . import nn
  File "/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/research/nn/__init__.py", line 1, in <module>
    from .modules import LinearFP8Mixed, LinearFP8Global
  File "/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/research/nn/modules.py", line 8, in <module>
    from bitsandbytes.optim import GlobalOptimManager
  File "/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/optim/__init__.py", line 6, in <module>
    from bitsandbytes.cextension import COMPILED_WITH_CUDA
  File "/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/cextension.py", line 20, in <module>
    raise RuntimeError('''
RuntimeError: 
        CUDA Setup failed despite GPU being available. Please run the following command to get more information:

        python -m bitsandbytes

        Inspect the output of the command and see if you can locate CUDA libraries. You might need to add them
        to your LD_LIBRARY_PATH. If you suspect a bug, please take the information from python -m bitsandbytes
        and open an issue at: https://github.com/TimDettmers/bitsandbytes/issues
```

OK, fail. Good news (!?) is that it looks like the same fail from inside of the docker container. I think it can't find the system CUDA 11.4. Maybe I was setting LD_LIBRARY_PATH in the original venv that I replaced with the clean one?. Let's try setting it:

```text
(test-venv)$ ls /usr/local
bin  cuda  cuda-11  cuda-11.4  etc  games  include  lib  man  sbin  share  src

(test-venv)$ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-11.4
(test-venv)$ python -m bitsandbytes
```

OK, same error. Won't past it again, it's identical. Let's follow the advice to override the PyTorch CUDA version, question is, do we override it to 114 (the actual system CUDA version or 117, the version bitsandbytes was built for). Let's try 11.7 first, since this is also matches our torch compatibility.

```text
(test-venv)$ export BNB_CUDA_VERSION=117
(test-venv)$ python -m bitsandbytes
```

Still no. Same fail. Another possibility is that we have moved the bitsandbytes directory into the bartelby repo and so maybe it needs to be rebuilt in place? I kind of doubt this, since it definitely worked before, but I wonder if some env vars were set or something from the original build which didn't survive the new venv or a reboot or something? Let's reboot now. See what happens. If it's still a no-go we will rebuild and reinstall bitsandbytes from the copy inside of bartleby.

```text
CUDA_VERSION=118 make cuda11x_nomatmul_kepler
python setup.py install
```

And finally:

```text
(test-venv)$ python -m bitsandbytes
```

Still fails. Let's try setting those environment vars again.

```text
(test-venv)$ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-11.4
(test-venv)$ python -m bitsandbytes
```

Nope, and this one:

```text
(test-venv)$ export BNB_CUDA_VERSION=118
(test-venv)$ python -m bitsandbytes
```

Still no - now I'm not sure as to the build flag that actually worked - was it 118 or 117. This is a nightmare.

After doing a reboot and:

```text
CUDA_VERSION=118 make cuda11x_nomatmul_kepler
python setup.py install
```

Without LD_LIBRARY_PATH or BNB_CUDA_VERSION set, we are now getting complaints about missing scipy when trying to run the bitsandbytes test. I think this is farther than we were getting a moment ago. Let's add scipy to the venv and try again:

```text
(test-venv)$ pip install scipy
(test-venv)$ python -m bitsandbytes

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ BUG REPORT INFORMATION ++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

++++++++++++++++++ /usr/local CUDA PATHS +++++++++++++++++++
/usr/local/cuda-11.4/targets/x86_64-linux/lib/stubs/libcuda.so
/usr/local/cuda-11.4/targets/x86_64-linux/lib/libcudart.so

+++++++++++++++ WORKING DIRECTORY CUDA PATHS +++++++++++++++
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda_linalg.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda_cu.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda_cpp.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/torch/lib/libc10_cuda.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda114.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda114_nocublaslt.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda117.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda118.so
/mnt/arkk/bartleby/.venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes/build/lib/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/mnt/arkk/bartleby/test-venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda_linalg.so
/mnt/arkk/bartleby/test-venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda_cu.so
/mnt/arkk/bartleby/test-venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda_cpp.so
/mnt/arkk/bartleby/test-venv/lib/python3.8/site-packages/torch/lib/libtorch_cuda.so
/mnt/arkk/bartleby/test-venv/lib/python3.8/site-packages/torch/lib/libc10_cuda.so
/mnt/arkk/bartleby/test-venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/mnt/arkk/bartleby/test-venv/lib/python3.8/site-packages/bitsandbytes-0.41.2-py3.8.egg/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so

++++++++++++++++++ LD_LIBRARY CUDA PATHS +++++++++++++++++++

++++++++++++++++++++++++++ OTHER +++++++++++++++++++++++++++
COMPILED_WITH_CUDA = True
COMPUTE_CAPABILITIES_PER_GPU = ['6.1', '3.7', '3.7']
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++ DEBUG INFO END ++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Running a quick check that:
    + library is importable
    + CUDA function is callable


WARNING: Please be sure to sanitize sensible info from any such env vars!

SUCCESS!
Installation was successful!
```

Well holy Hall Effect folks, I think we did it. Not sure what we did, but we did it. Let's make sure that bartleby runs from this venv and then wipe it and start over so that we are sure that we know exactly what steps worked.

So, bartleby works, but we get a warning about serializing 4 bit models and that we should upgrade bitsandbytes to >=0.41.3. Most recent release is 0.43.0. Guess we should upgrade. Reboot for a clean slate and here we go:

### 9. Bitsandbytes upgrade

```text
git clone https://github.com/TimDettmers/bitsandbytes.git
```

And restart the install with a fresh venv. This time, let's try starting with a specific torch version and then just installing everything else however pip wants. First, set the google credentials path:

```text
export GOOGLE_APPLICATION_CREDENTIALS="bartleby/credentials/service_key.json"
pip install torch==1.13.1
pip install transformers
pip install discord.py
pip install matrix-nio
pip install google-api-core
pip install python-docx
pip install google-api-python-client
pip install SentencePiece
pip install accelerate
pip install scipy
```

Now bitsandbytes. First, let's make a build venv - looks like we need cmake and some other stuff for to build the newer version of bitsandbytes:

```text
python3 -m venv bnb-build-venv
cd bitsandbytes
pip install --upgrade pip
pip install cmake --upgrade
pip install -r requirements-dev.txt
```

Pip fails when installing scipy - looks like the most recent version it can find is 1.10.1, while bitsandbytes asks for 1.11.4. Weird, 1.10.1 looks to the the current version on the scipy site. Does that need a source build too? Gosh. Let's try just removing that version pin from the requirements-dev.txt.

```text
pip install -r requirements-dev.txt
```

Ok, same thing for pandas - are these all like pre-release versions or something?

Removing the version pins for scipy, pandas and matplotlib allowed pip to finish, but I'm not hopeful that this will work - saw a bunch of nvidia cu12 stuff getting pulled in. We might have to stick to an earlier version of bitsandbytes. Let's at least try and see it through.

```text
cmake -DCOMPUTE_BACKEND=cuda -S .
CUDA_VERSION=118 make
```

Again, not confident. Repo documentation mentions using the cuda11x_nomatmul_kepler make target, but make complains it's not found... Let's see what happens.

Now switch to the test-venv to install

```text
pip install .
python -m bitsandbytes
```

Nope.

OK, but wait, when installing I got: Successfully installed bitsandbytes-0.44.0.dev0 - I think we cloned the wrong thing. Let's try that again with the 0.43.0 release.

First, switch to the 0.43.0 tag on github and clone again. In a fresh venv:

```text
git clone https://github.com/TimDettmers/bitsandbytes.git
mv bitsandbytes bitsandbytes-43
pip install --upgrade pip
pip install cmake --upgrade
pip install -r requirements-dev.txt
```

OK, F-this, still getting issues with not found versions of common packages. Looks like it needs python 3.13. Let's step back to version 42 - that seems to be the last one before they changed the install and started using cmake.

Nuke the venv-bnb-build environment and try this from the 0.42.0 tag in the bitsandbytes github repo:

```text
(test-venv)$ git clone https://github.com/TimDettmers/bitsandbytes.git
(test-venv)$ mv bitsandbytes bitsandbytes-42
(test-venv)$ cd bitsandbytes-42
(test-venv)$ CUDA_VERSION=118 make cuda11x_nomatmul_kepler

make: *** No rule to make target 'cuda11x_nomatmul_kepler'.  Stop.
```

Arrgghhh, same problem. Frustrating because the documentation says to use that flag for kepler cards. Looks like maybe they removed it and didn't update to docs. Let's step back another version to 0.41.0 and try again.

OK - wait, I think I have been downloading the same wrong thing the whole time. The clone URL is always the same and points to that 44-dev version. Dummy. Let's download the latest release as a tarball and see what happens.

```text
wget https://github.com/TimDettmers/bitsandbytes/archive/refs/tags/0.43.0.tar.gz
cd bitsandbytes-0.43.0
```

Make, activate and update a dev environment:

```text
python3 -m venv venv-bnb-build
pip install --upgrade pip
source /venv-bnb-build/bin/activate
```

Install build dependencies:

```text
pip install cmake --upgrade
pip install -r requirements-dev.txt
```

Ok, still having issues with scipy 1.11.1 for python 3.13. Let's try the tarball for version 42. Our build venv is still clean except for the pip upgrade and cmake, so let's just reuse it:

```text
wget https://github.com/TimDettmers/bitsandbytes/archive/refs/tags/0.42.0.tar.gz
tar -xf 0.42.0.tar.gz
cd bitsandbytes-0.42.0
CUDA_VERSION=118 make cuda11x_nomatmul_kepler
python setup.py install
```

OK, at this point running the bitsandbytes test starts complaining about missing modules, starting with torch. I think that's actually a good sign. This thing is a mess, so let's start over one more time. Reboot, nuke the venvs and, install the 42 version fresh in a  new bartleby test venv.

```text
python3 -m venv venv-test
pip install --upgrade pip
export GOOGLE_APPLICATION_CREDENTIALS="bartleby/credentials/service_key.json"
pip install torch==1.13.1
pip install transformers
pip install discord.py
pip install matrix-nio
pip install google-api-core
pip install python-docx
pip install google-api-python-client
pip install SentencePiece
pip install accelerate
pip install scipy
pip install Jinja2
```

Now bitsandbytes 0.42.0:

```text
cd bitsandbytes-0.42.0
CUDA_VERSION=118 make cuda11x_nomatmul_kepler
python setup.py install
```

Not working, I dunno. Running out of ideas. Let's try:

```text
CUDA_VERSION=117 make cuda11x_nomatmul_kepler
python setup.py install
python -m bitsandbytes
```

My gosh, it worked!

```text
++++++++++++++++++ BUG REPORT INFORMATION ++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

++++++++++++++++++ /usr/local CUDA PATHS +++++++++++++++++++
/usr/local/cuda-11.4/targets/x86_64-linux/lib/stubs/libcuda.so
/usr/local/cuda-11.4/targets/x86_64-linux/lib/libcudart.so

+++++++++++++++ WORKING DIRECTORY CUDA PATHS +++++++++++++++
/mnt/arkk/bartleby/bitsandbytes-0.42.0/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes-0.42.0/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes-0.42.0/build/lib/bitsandbytes/libbitsandbytes_cuda118_nocublaslt.so

++++++++++++++++++ LD_LIBRARY CUDA PATHS +++++++++++++++++++

++++++++++++++++++++++++++ OTHER +++++++++++++++++++++++++++
COMPILED_WITH_CUDA = True
COMPUTE_CAPABILITIES_PER_GPU = ['6.1', '3.7', '3.7']
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++ DEBUG INFO END ++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Running a quick check that:
    + library is importable
    + CUDA function is callable


WARNING: Please be sure to sanitize sensible info from any such env vars!

SUCCESS!
Installation was successful!
```

Argh, I'm almost mad that it worked and I have no idea why, that 118 vs 117 in the make target flag is killing me. Seems like sometimes one works and not the other and sometimes it's the other way around. Do we need to make twice or something? Let's nuke everything one more time and do it again from scratch after a reboot.

### 10. Verify solution end to end

New venv:

```text
python3 -m venv venv-test
source venv-test/bin/activate
pip install --upgrade pip
```

Dependencies:

```text
pip install torch==1.13.1
pip install transformers
pip install discord.py
pip install matrix-nio
pip install google-api-core
pip install python-docx
pip install google-api-python-client
pip install SentencePiece
pip install accelerate
pip install scipy
pip install Jinja2
```

Bitsandbytes

```text
wget https://github.com/TimDettmers/bitsandbytes/archive/refs/tags/0.42.0.tar.gz
tar -xf 0.42.0.tar.gz
cd bitsandbytes-0.42.0
CUDA_VERSION=117 make cuda11x_nomatmul_kepler
python setup.py install
python -m bitsandbytes
```

Hay, whatdaya know?! It still works!

```text
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ BUG REPORT INFORMATION ++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

++++++++++++++++++ /usr/local CUDA PATHS +++++++++++++++++++
/usr/local/cuda-11.4/targets/x86_64-linux/lib/stubs/libcuda.so
/usr/local/cuda-11.4/targets/x86_64-linux/lib/libcudart.so

+++++++++++++++ WORKING DIRECTORY CUDA PATHS +++++++++++++++
/mnt/arkk/bartleby/bitsandbytes-0.42.0/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes-0.42.0/build/lib/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so

++++++++++++++++++ LD_LIBRARY CUDA PATHS +++++++++++++++++++

++++++++++++++++++++++++++ OTHER +++++++++++++++++++++++++++
COMPILED_WITH_CUDA = True
COMPUTE_CAPABILITIES_PER_GPU = ['6.1', '3.7', '3.7']
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++ DEBUG INFO END ++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Running a quick check that:
    + library is importable
    + CUDA function is callable


WARNING: Please be sure to sanitize sensible info from any such env vars!

SUCCESS!
Installation was successful!
```

OK, I think we got it. Let's button this thing up.

### 11. Finalize and containerize

This is the home stretch. Here is what we need to do:

1. Set-up our real venv
2. Update the docker file
3. Build the image with default GPU 0
4. Run and test
5. Push to docker hub
6. Update install instructions and docker hub documentation
7. Re-build the image with GPU 2 for local production run
8. Profit?

#### Final Dockerfile

Going to try using requierments.txt to make the image instead of a bunch of individual pip installs. Also, will want a known good, updated & clean venv to use throughout the project. So, let's make one.

Back up the old venv:

```text
source .venv/bin/activate
pip freeze > requirements-bak.txt
deactivate
mv .venv .venv-bak
```

Make, activate and update a new venv:

```text
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

Install dependencies:

```text
pip install torch==1.13.1
pip install transformers
pip install discord.py
pip install matrix-nio
pip install google-api-core
pip install python-docx
pip install google-api-python-client
pip install SentencePiece
pip install accelerate
pip install scipy
pip install Jinja2
```

Then, freeze the venv before installing bitsandbytes, because we want to build that from source and install it manually.

```text
pip freeze > requirements.txt
```

Now, get and unpack the bitsandbytes 0.42.0 source:

```text
wget https://github.com/TimDettmers/bitsandbytes/archive/refs/tags/0.42.0.tar.gz
tar -xf 0.42.0.tar.gz
cd bitsandbytes-0.42.0
```

Build and install:

```text
CUDA_VERSION=117 make cuda11x_nomatmul_kepler
python setup.py install
python -m bitsandbytes
```

Works!

```text
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ BUG REPORT INFORMATION ++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

++++++++++++++++++ /usr/local CUDA PATHS +++++++++++++++++++
/usr/local/cuda-11.4/targets/x86_64-linux/lib/stubs/libcuda.so
/usr/local/cuda-11.4/targets/x86_64-linux/lib/libcudart.so

+++++++++++++++ WORKING DIRECTORY CUDA PATHS +++++++++++++++
/mnt/arkk/bartleby/bitsandbytes-0.42.0/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so
/mnt/arkk/bartleby/bitsandbytes-0.42.0/build/lib/bitsandbytes/libbitsandbytes_cuda117_nocublaslt.so

++++++++++++++++++ LD_LIBRARY CUDA PATHS +++++++++++++++++++

++++++++++++++++++++++++++ OTHER +++++++++++++++++++++++++++
COMPILED_WITH_CUDA = True
COMPUTE_CAPABILITIES_PER_GPU = ['6.1', '3.7', '3.7']
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++ DEBUG INFO END ++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Running a quick check that:
    + library is importable
    + CUDA function is callable


WARNING: Please be sure to sanitize sensible info from any such env vars!

SUCCESS!
Installation was successful!
```

Test bartleby:

```text
cd ../
export GOOGLE_APPLICATION_CREDENTIALS="bartleby/credentials/service_key.json"
python -m bartleby
```

Works great. Check .dockerignore. Here are our additions:

```text
.venv
.venv-bak
.vscode
.dockerignore
.gitignore
bartleby.service
bitsandbytes-0.42.0.tar.gz
docker_hub_info.md
docker_setup_notes.md
docker_setup.md
bartleby/hf_cache
bartleby/logs
bartleby/credentials
Dockerfile
requirements-bak.txt
```

Here is the Dockerfile:

```text
FROM nvidia/cuda:11.4.3-runtime-ubuntu20.04

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set location of Google service account credentials
ENV GOOGLE_APPLICATION_CREDENTIALS="/bartleby/bartleby/credentials/service_key.json"

# Set working directory
WORKDIR /

# Install python 3.8 & pip
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

# Move the bartleby source code in
WORKDIR /bartleby
COPY . /bartleby

# Make an empty credentials folder for mounting inside of bartleby
RUN mkdir /bartleby/bartleby/credentials

# Install dependencies
RUN pip install -r requirements.txt

# Install bitsandbytes
WORKDIR /bartleby/bitsandbytes-0.42.0 
RUN python3 setup.py install

# Run bartleby
WORKDIR /bartleby
CMD ["python3", "-m", "bartleby"]
```

Clean up docker, build the image and start the container:

```text
docker system prune
docker build -t gperdrizet/bartleby:backdrop_launch .
docker run --gpus all --mount type=bind,source="$(pwd)"/bartleby/credentials,target=/bartleby/bartleby/credentials --name bartleby -d gperdrizet/bartleby:backdrop_launch
```

Works! Pus it to Docker Hub:

```text
docker push gperdrizet/bartleby:backdrop_launch
```

Now just build a new image with GPU 2 set in configuration.py so it runs localy on one of the K80s.

Victory!
