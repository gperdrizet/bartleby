# Docker setup

Plan is to containerize bartleby for deployment using following the Docker [instructions for containerizing python apps](https://docs.docker.com/language/python/containerize/).

## 1. Docker setup

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
|   2  NVIDIA GeForce ...  On   | 00000000:07:00.0 Off |                  N/A |
|  0%   47C    P8    10W / 151W |      1MiB /  8118MiB |      0%      Default |
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

# # Set-up CUDA and the CUDA toolkit
# RUN apt-get install -y wget
# RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
# RUN mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
# RUN wget https://developer.download.nvidia.com/compute/cuda/11.4.0/local_installers/cuda-repo-ubuntu2004-11-4-local_11.4.0-470.42.01-1_amd64.deb
# RUN dpkg -i cuda-repo-ubuntu2004-11-4-local_11.4.0-470.42.01-1_amd64.deb
# RUN apt-key add /var/cuda-repo-ubuntu2004-11-4-local/7fa2af80.pub
# RUN apt-get update -y
# RUN apt-get install -y cuda
# RUN apt-get install -y nvidia-cuda-toolkit

# # Set path to correct CUDA version
# ENV export PATH=/usr/local/cuda-11.4/bin${PATH:+:${PATH}}

# # Build and install bitsandbytes
# WORKDIR /bartleby/bitsandbytes
# RUN CUDA_VERSION=118 make cuda11x_nomatmul_kepler
# RUN python3 setup.py install

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

Done!

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

OK, what have we learned - still not really sure exactly what the difference between the base and runtime images are, but the devel image looks just like my host system install from inside the container. Nvidia-smi reports 470 driver and CUDA 11.4 and nvcc reports 11.4/11.4. However, although building and installing bitsandbytes from the Dockerfile appears to work python3 -m bitsandbytes inside the container fails with what looks like a bunch of path issues. Coulden't figure it out. Let's try building and installing from inside the running container.

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

Here is the setup for a CPU only image:

1. Uncomment everything in requirements except bitsandbytes
2. Comment out the individual installs of torch and scipy
3. Edit config and set quantization to none and device map to cpu

Next steps will be to:

1. Not put secrets in the image - need to learn how to do this correctly
2. Do a better job of pruning requirements
3. Maybe make it a multi-stage build
