# Bartleby

[Bartleby](https://github.com/gperdrizet/bartleby/blob/logging/bartleby/data/bartleby.jpg)

Bartleby is a LLM chatbot and writing assistant written in Python using [HuggingFace](https://huggingface.co/). The project goal is to create a conversational writing assistant which interacts naturally via a chat interface and creates documents in docx format. A 'universal' interface was achieved using the Matrix protocol (i.e. the user can interact with the Bartleby via any matrix chat client application using any device: phone, laptop or tablet running: macOS, Windows, Linux, android, IOS etc,). Documents are created and accessed via Google Drive using Google Cloud Platform APIs. Bartleby can also run in an interactive text-only mode via the terminal.

Bartleby exposes a number of system control commands via the chat interface. System control commands allow the user to manipulate generation parameters, alter prompting behavior and make and save documents on the fly from any device.

## Available models

1. [zephyr-7b-beta](https://huggingface.co/HuggingFaceH4/zephyr-7b-beta)
2. [falcon-7b-instruct](https://huggingface.co/tiiuae/falcon-7b-instruct)

Bartleby is easily extensible to new models and should work out-of-the-box with any Mistral or Falcon family models available via HuggingFace.

## Prerequisites

1. Access to a matrix server with the ability to create a room and user for Bartleby.
2. A google developer account with an active service account which has edit access to a google drive folder.
3. Python 3+ with Huggingface transformers.
