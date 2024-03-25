# Containerization

## 1. Docker setup

Start with a fresh, up-to-date docker install if needed. From the [Ubuntu install instructions](https://docs.docker.com/engine/install/ubuntu/).

Remove old install:

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

Finally, set up log rotation. Add the following to */etc/docker/daemon.json*, creating the file if it doesn't exist. The data-root parameter is not necessary, omit it to accept the system default or set is to an alternative location.

```json
{
    "data-root": "/mnt/fast_scratch/docker",
    "log-driver": "json-file",
    "log-opts": {
        "max-file": "3",
        "max-size": "10m"
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

This will make changes to */etc/docker/daemon.json*, adding the *runtimes* stanza:

```json
{
    "data-root": "/mnt/fast_scratch/docker",
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

Dockerfile:

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

Added the following to .dockerignore:

```text
LICENSE
README.md
NOTES.md
architecture.md
docker_setup_notes.md
bartleby/hf_cache
bartleby/logs
bartleby/credentials
```

Build the image and push to Docker Hub, then remove the local copy and clean up.

```text
docker build -t gperdrizet/bartleby:latest .
docker push gperdrizet/bartleby:latest
docker rmi gperdrizet/bartleby:latest
docker system prune
```

Then pull the image and run it:

```text
docker pull gperdrizet/bartleby:latest
docker run --restart always --gpus all --mount type=bind,source="$(pwd)"/bartleby/credentials,target=/bartleby/bartleby/credentials --name bartleby -d gperdrizet/bartleby:latest
```

Include the *--restart always* flag to restart the container on reboot or crash or daemon restart.

Successful round trip. Done!
