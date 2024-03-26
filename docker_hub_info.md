# Bartleby Docker Images

## Summary

LLM collaborator on Discord and Matrix. Running HuggingFace: zephyr, falcon or DialoGPT.

## Repository overview

Images in this repository require the [Nvidia Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) to run and were designed for Kepler GPUs. The images may run on more modern hardware, but may not take full advantage of later CUDA compute capabilities. The models are loaded with 4 bit quantization via [BitsandBytes](https://github.com/TimDettmers/bitsandbytes) and require ~6 GB of GPU memory. Containers must also mount a 'credentials' directory which contains keys, tokens etc. for the relevant accounts. The instructions below assume Ubuntu 20.04 and a working Docker (tested with 26.0.0).

### 1. Nvidia Container Toolkit set-up

First, add the repo:

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

Finally, configure docker and restart the daemon:

```text
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

This will make changes to */etc/docker/daemon.json*, adding the *runtimes* stanza:

```json
{
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

### 2. Credentials

Make a directory for your credentials somewhere safe that the container can mount. This directory needs to contain the files described in the *credentials* directory of the [project GitHub repo](https://github.com/gperdrizet/bartleby/tree/main/bartleby/credentials).

### 3. Run

Pull the image:

```text
docker pull gperdrizet/bartleby:backdrop_launch
```

Run the image. Replace \<CREDENTIALS\> with the path to your credentials directory:

```text
docker run --gpus all --mount type=bind,source=<CREDENTIALS>,target=/bartleby/bartleby/credentials --name bartleby -d gperdrizet/bartleby:backdrop_launch
```

That's it! The first response from bartleby may be slow because the model(s) are pulled from HuggingFace the first time they are used.
