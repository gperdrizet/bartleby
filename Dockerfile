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

# Make an empty credentials folder for bindmount
RUN mkdir /bartleby/bartleby/credentials

# Make a volumme for models so we don't have to
# pull them from HuggingFace every time
VOLUME bartleby/hf_cache

# Install dependencies
RUN pip install -r requirements.txt

# Install bitsandbytes
WORKDIR /bartleby/bitsandbytes-0.42.0 
RUN python3 setup.py install

# Run bartleby
WORKDIR /bartleby
CMD ["python3", "-m", "bartleby"]