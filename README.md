# Bartleby

## News

- **Bartleby named finalist** in Backdrop Build V3 build challenge! See [bartleby's build page](https://backdropbuild.com/builds/v3/bartleby) on Backdrop.

- **Bartleby live on Discord!** Use [this invite link](https://discord.com/oauth2/authorize?client_id=1217547475615744015&permissions=0&scope=bot) to add bartleby to your server.

- **Bartleby Docker image available!** See [gperdrizet/bartleby on Docker Hub](https://hub.docker.com/repository/docker/gperdrizet/bartleby/general).

<p align="center">
    <img width="512" src=https://github.com/gperdrizet/bartleby/blob/logging/bartleby/data/bartleby.jpg>
</p>

Bartleby is a LLM based conversational collaborator written in Python using [HuggingFace](https://huggingface.co/) transformers, [discord.py](https://discordpy.readthedocs.io/en/stable/), [matrix-nio](https://matrix-nio.readthedocs.io/en/latest/index.html) and [google-api-core](https://googleapis.dev/python/google-api-core/latest/index.html) among others. The project goal is to create an open source, conversational writing assistant which interacts naturally via a chat interface and can generate documents in docx format. A 'universal' interface was achieved using Discord (i.e. the user can interact with the Bartleby via any Discord client application using any device: phone, laptop or tablet running: macOS, Windows, Linux, Android, IOS etc,). Bartleby can also interact via a Matrix server. Documents are created and accessed via Google Drive using Google Cloud Platform APIs.

Bartleby exposes a number of system control commands via the chat interface. System control commands allow the user to manipulate generation parameters, alter prompting behavior and make and save documents on the fly from any device.

## Table of contents

1. Features
2. Where to find bartleby
3. Usage
4. How to run bartleby
5. Command reference

## 1. Features

- **Easily accessible** on Discord or Matrix - you can interact with bartleby via apps many people already use for communication and collaboration.
- **Configurable/tweak-able** - bartleby exposes system commands though agent-like functionality and chat commands. For example, you can set individual parameters in the underlying [transformers GenerationConfig class]([transformers GenerationConfiguration class](https://github.com/huggingface/transformers/blob/v4.39.1/src/transformers/generation/configuration_utils.py#L62)) via Discord slash commands or just tell bartleby in plain english what model you want to use.
- **Generates Google Docs** from chat and saves to user specified shared folder.
- **Open source models** - bartleby is not beholden to proprietary APIs and can take advantage of the many new models constantly being released by the open source community on HuggingFace.
- **Open source codebase** - bartleby is an open source project. Clone it, fork it, extend it, modify it, host it yourself and use it the way you want to use it.

## 2. Where to find bartleby

Bartleby is most feature-complete and publicly available on Discord. If you are interested in trying it out, I recommend doing so there. You can add it to your server [here](https://discord.com/oauth2/authorize?client_id=1217547475615744015&permissions=0&scope=bot).

There is also a Docker image available on [Docker Hub](https://hub.docker.com/repository/docker/gperdrizet/bartleby/general).

Bartleby is also compatible with the Matrix protocol. If you would like to run it on Matrix, you will need to host the bot yourself and add it to a Matrix server to which you have admin access (see below).

## 3. Usage

The goal of the following instructions is to provide a quick jump-start to interacting with some of bartleby's features in a discord server. For more details about configuring and running it yourself see ‘How to run bartleby’ below. For a complete list of commands see 'Command reference' below.

### 3.1. Talking to bartleby

Bartleby is aware of the active user count in a discord channel and interacts accordingly. If you are in a channel alone with it, just start posting. Bartleby will reply to any messages in the channel. In a channel with multiple other users, bartleby will only respond to mentions or direct replies. The first time you message, use a mention (@bartleby) to get the bot's attention. After that, you can mention or reply as you like to keep the conversation going. Bartleby can also use threads - in a private thread, you do not need to use mentions or replies, bartleby will respond as if the conversation were happening in a channel with no other users.

### 3.2. The command interface

Bartleby has a bunch of control commands that are accessible via the chat. These give a large degree of control over how the bot and model(s) behave. The commands allow you to do things like change the prompt, update the decoding strategy, set generation configuration parameters and even swap the underlying model. There are three ways to access commands on Discord:

1. **Natural language text**: bartleby has some agent-like functionality built in. It uses a ‘helper’ T5 model fine-tuned to recognize user intent for a subset of available commands. Try ‘@bartleby What models do you support?’ or ‘@bartleby Use the last 10 messages as input.’
2. **Discord slash commands**: bartleby’s complete set of commands are registered to the Discord app command system. Start typing ‘/’ in the chat to bring up a context menu of the available commands.
3. **Chat commands**: the same set of commands are also available using the ‘--’ flag in chat, e.g. ‘--set-config max_new_tokens 128’. This modality is not necessary for discord - it's redundant to the slash commands and only exists for compatibility with other chat applications.

See the command reference below for a complete list of commands.

### 3.3. Saving documents

Bartleby is intended to be a LLM writing and thinking collaborator and as such, can interact with Google Drive. Documents are saved from the chat to a shared Google Drive folder in docx format. The steps to generate and save a document to Google Drive are as follows:

1. **Set a shared folder**. Create a folder on gdrive for bartleby to save documents in and copy its share link. Then submit  /set_gdrive_folder YOUR_SHARE_LINK command in chat. You only need to do this once per session.
2. **Set a title**, if desired. Use /set_document_title YOUR_TITLE in chat or try something like, '@bartleby call the document War and Peace' to set the title. Spaces are fine, and no need to quote. This title will be used as the file name and document title of all subsequent uploads until a new title is set. If no title is set, documents will be uploaded as 'bartleby_text.docx'.
3. **Generate the document**. /make_docx or something like ‘@bartleby save that output to gdrive’ will upload the last message in chat. Or, if you want to capture an earlier message, right click on it and select ‘apps’ > ‘Save to gdrive’ from the context menu (Discord only).

## 4. How to run bartleby

### 4.1. Prerequisites

1. Nvidia GPU with >=~ 5 GB memory (depending on which model you pick to run).
2. ~30 GB disk space for models, assuming you want to try all of those currently available. Or ~15 GB for just the current default falcon-7b.
3. Nvidia driver, CUDA and the CUDA toolkit (Build/tested with Kepler card on 470 driver with CUDA runtime/driver 11.4/11.4).

### 4.2. Via Docker

The easiest way to run bartleby is by pulling the *gperdrizet/bartleby:backdrop_launch* image from Docker Hub. Follow the instructions in the repository overview to get it up and running.

### 4.3. Via Python venv

If you prefer to run bartleby on bare metal, without a container, you can use this repo and the included *requirements.txt*. The version pins in *requirements.txt* produce a venv which works for a Nvidia Kepler GPU running the 470 driver and CUDA 11.4/11.4 with compute capability 3.7. If you are using a newer card, pip installing *requierments.txt* may still work, but will not take advantage of later CUDA compute capabilities. If you have a more modern graphics card, consider installing the following minimal dependencies manualy. They should pull in everything else that is needed. The trickiest part of the install is getting bitsandbytes to play nice with older cards. If you are working with modern hardware this may not be an issue. Otherwise, you may have to build bitsandbytes from source.

#### Setup instructions

Clone the repo:

```text
git clone https://github.com/gperdrizet/bartleby.git
cd bartleby
```

Make a fresh virtual environment with Python 3.8.

```text
python3.8 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

#### Dependencies option A: 'modern' GPUs (CUDA >=12)

Install the following via pip in the virtual environment:

```text
pip install torch
pip install transformers
pip install discord.py
pip install matrix-nio
pip install google-api-core
pip install python-docx
pip install google-api-python-client
pip install sentencepiece
pip install jinja2
pip install accelerate
pip install scipy
pip install bitsandbytes
```

#### Dependencies, option B: Kepler GPUs (CUDA 11.4)

Main difference here is extreme caution in regard to versioning versioning - newer versions of things like torch will cause problems for older cards. The correct version of bitsandbytes must be built from source correctly so that it plays nice with everything else.

First, install *requierments.txt* in the virtual environment created above:

```text
pip install -r requirements.txt
```

Then, clone, build and install bitsandbytes 0.42.0. It does not matter where you put the bitsandbytes directory, so long as you run the install command from bartleby's activated virtual environment.

Yes, CUDA_VERSION=117 is correct.

```text
wget https://github.com/TimDettmers/bitsandbytes/archive/refs/tags/0.42.0.tar.gz
tar -xf 0.42.0.tar.gz
cd bitsandbytes-0.42.0
```

Build, install and test:

```text
CUDA_VERSION=117 make cuda11x_nomatmul_kepler
python setup.py install
python -m bitsandbytes
```

#### Credentials/secrets

Take a look at the credentials directory under *bartleby/*. It contains several 'SAMPLE' files describing what credentials are needed for the various accounts associated with bartleby.

The *client_secret_apps...* file and the *service_key* file are required - they contain the credentials for Google Cloud.

You additionally need either Matrix or Discord credentials depending on where you will run the bot. See the respective 'SAMPLE' files for descriptions of what exactly each file needs to contain.

#### Configuration

Have a look and configuration.py. It may need some changes depending on your system and intent:

1. **MODE**: default to 'discord', set to 'matrix' if that's what you want.
2. **CUDA_VISIBLE_DEVICES**: If you have only one GPU, set this to 0 or comment out the whole line, if you have multiple GPUs, set it to whichever you want bartleby to use. If you are using a multi-GPU system you can also play with *device_map*, setting sequential or auto, but in my experience generation is fastest when the model is pinned to a specific GPU (e.g. 'cuda:0'). Also, if you have a ton of VRAM you can set *quantization* to none for a speed boost at the price of a larger memory footprint.
3. **CPU_threads**: Set this to the number of physical cores you have (or less).

#### Run

From your clone's root directory:

```text
python -m bartleby
```

## 5. Command reference

### 4.1. System commands

| chat command                 | discord slash command         | system agent command | action                                                                                  |
|------------------------------|-------------------------------|----------------------|-----------------------------------------------------------------------------------------|
| --commands                   | /commands                     | Yes                  | Posts list of available chat commands                                                   |
| --input-buffer-size          | /input_buffer_size            | Yes                  | Posts the number of most recent chat messages currently being used as input the the LLM |
| --set-input-buffer-size N    | /set_input_buffer_size N      | Yes                  | Sets the number of most recent chat messages to use as input for the LLM to N           |
| --input-messages             | /input_messages               | No                   | Posts the current contents of the LLM input buffer in chat                              |
| --prompt                     | /prompt                       | Yes                  | Posts the current initial system prompt used to start each conversation                 |
| --set-prompt PROMPT          | /set_prompt PROMPT            | No                   | Sets initial system prompt used to start new conversations to PROMPT                    |
| --reset-chat                 | /reset_chat                   | Yes                  | Clears message history and starts a new conversation                                    |

### 4.2. Generation commands

| chat command                 | discord slash command         | system agent command | action                                                                                  |
|------------------------------|-------------------------------|----------------------|-----------------------------------------------------------------------------------------|
| --decoding-mode              | /decoding_mode                | No                   | Post the current generation decoding mode to chat                                       |
| --decoding-modes             | /decoding_modes               | No                   | Posts the list of available generation decoding mode presets to chat                    |
| --set-decoding-mode MODE     | /set_decoding_mode MODE       | No                   | Sets generation decoding mode to MODE where mode is one of the available presets        |
| --config                     | /config                       | Yes                  | Posts any values from transformers.GenerationConfig not currently set to model defaults |
| --config-full                | /config_full                  | No                   | Posts all values from transformers.GenerationConfig                                     |
| --set-config X Y             | /set_config X Y               | No (except temp. and max new tokens) | Updates the value of any parameter X from transformers.GenerationConfig to Y |
| --model                      | /show_current_model           | No                   | Post the name of the model currently being used for generation                          |
| --models                     | /models                       | Yes                  | Post the list of available models to chat                                               |
| --swap-model MODEL           | /swap_model MODEL             | Yes                  | Changes the LLM being used for response generation to MODEL from supported model list   |

### 4.3. Document commands

| chat command                 | discord slash command         | system agent command | action                                                                                  |
|------------------------------|-------------------------------|----------------------|-----------------------------------------------------------------------------------------|
| --document-title             | /document_title               | Yes                  | Posts the current document title, used for saving output to gdrive, in chat             |
| --set-document-title TITLE   | /set_document_title TITLE     | Yes                  | Sets the document title that will be used to save output to gdrive                      |
| --set-gdrive-folder LINK     | /set_gdrive_folder LINK       | No                   | Sets the target gdrive folder used for document uploads to LINK where link is a google drive folder share link |
| --make-docx N                | /make_docx (no argument)      | Yes                  | Makes a docx file using document title for title and filename, uploads it to gdrive using a previously provided share link. Chat command takes integer N specifying how many most recent messages to include, discord slash command takes no arguments and generates document from the most recent message. |

## 5. Available models

1. [zephyr-7b-beta](https://huggingface.co/HuggingFaceH4/zephyr-7b-beta)
2. [falcon-7b-instruct](https://huggingface.co/tiiuae/falcon-7b-instruct)

If you want to add a new model from HuggingFace, take a look at *model_prompting_functions.py* in *bartleby/functions*. Add a prompting function and a cognate *elif* stanza to the LLM class's *prompt_model* method. Then submit a pull request!
