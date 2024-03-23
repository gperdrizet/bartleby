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
# RUN pip install scipy==1.10.1
# RUN pip install torch==1.13.1

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