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
RUN pip install torch==1.13.1
RUN pip install transformers==4.37.2
RUN pip install discord.py==2.3.2
RUN pip install matrix-nio==0.24.0
RUN pip install google-api-core==2.17.0
RUN pip install python-docx==1.1.0
RUN pip install google-api-python-client==2.116.0
RUN pip install sentencepiece==0.2.0
RUN pip install Jinja2==3.1.3
RUN pip install accelerate==0.26.1
RUN pip install scipy==1.10.1

# Install bitsandbytes
WORKDIR /bartleby/bitsandbytes
RUN python3 setup.py install

# Run bartleby
WORKDIR /bartleby
CMD ["python3", "-m", "bartleby"]