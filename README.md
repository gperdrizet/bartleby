# Bartleby

## Bartleby is live on Discord! Use [this invite link](https://discord.com/oauth2/authorize?client_id=1217547475615744015&permissions=0&scope=bot) to add bartleby to your server

![Bartleby](https://github.com/gperdrizet/bartleby/blob/logging/bartleby/data/bartleby.jpg)

Bartleby is a LLM based conversational collaborator written in Python using [HuggingFace](https://huggingface.co/). The project goal is to create a conversational writing assistant which interacts naturally via a chat interface and creates documents in docx format. A 'universal' interface was achieved using Discord (i.e. the user can interact with the Bartleby via any Discord client application using any device: phone, laptop or tablet running: macOS, Windows, Linux, android, IOS etc,). Documents are created and accessed via Google Drive using Google Cloud Platform APIs.

Bartleby exposes a number of system control commands via the chat interface. System control commands allow the user to manipulate generation parameters, alter prompting behavior and make and save documents on the fly from any device.

## Table of contents

1. Features
2. Where to find bartleby
3. Usage
4. Command reference

## 1. Features

- Easily accessible on Discord or Matrix - you can interact with bartleby via apps many people already use for communication and collaboration.
- Configurable/tweak-able - bartleby exposes many system commands though agent-like functionality and a set of chat commands.
- Generates documents from chat and saves them to user specified shared Google Drive folder.
- Uses models from HuggingFace. Bartleby is not beholden to closed source models and can take advantage of the many new models constantly being released by the open source community.
- Open source - bartleby is an open source project. Clone it, fork it, extend it, modify it, host it yourself and use it the way you want to use it.

## 2. Where to find bartleby

Bartleby is most feature-complete and publicly available on Discord. If you are interested in trying it out, I recommend doing so there. You can add it to your server [here](https://discord.com/oauth2/authorize?client_id=1217547475615744015&permissions=0&scope=bot).

Bartleby is also compatible with the Matrix protocol. If you would like to run it on Matrix, you will need to host the bot yourself and add it to a Matrix server which you have admin access to (see below).

## 3. Usage

These instructions are to get you started interacting with some of bartleby’s features in a discord server. For more details about configuring and running it yourself see ‘How to run bartleby’ below.

### 3.1. Talking to bartleby

Bartleby is aware of how many people are in a given discord channel and interacts accordingly. If you are in a channel alone with it, you can just start posting. Bartleby assumes any messages are meant for him and will respond to anything posted. If you are in a channel with multiple other users, bartleby will only respond if he is mentioned or replied too. The first time you message, use a mention (@bartleby) to get its attention. Bartleby will post a response in the form of a reply to your message. After that, you can mention or reply as you like to keep the conversation going. Bartleby will also work if you take it into a thread - in that context you do not need to use mentions or replies, it will respond as if the conversation were happening in a channel with no other users.

### 3.2. The command interface

Bartleby has a bunch of control commands that are accessible via the chat. These give a large degree of control over how the model behaves. The commands allow you to do things like change the prompt, update the decoding strategy, set generation configuration parameters and even swap the underlying model. There are three ways to access commands on Discord:

1. Natural language text: bartleby has some agent-like functionality built in. It uses a ‘helper’ T5 model fine-tuned to recognize user intent for a subset of available commands. Try ‘@bartleby What models do you support?’ or ‘@bartleby Use the last 10 messages as input.’
2. Discord slash commands: bartleby’s complete set of commands are registered to the Discord app command system. Start typing ‘/’ to bring up a context menu of the available commands
3. Chat commands: the same set of commands are also available using the ‘--’ flag in chat, e.g. ‘--set-config max_new_tokens 128’.

See the command reference below for a complete list of commands and their functions.

### 3.3. Saving documents

Bartleby is intended to be a LLM based writing and thinking collaborator and as such can interact with Google Drive. Documents are saved from the chat to a shared Google Drive folder in docx format. Here are the steps to generate and save a document to Google Drive:

1. Set a shared folder. Create a folder on gdrive for bartleby to save documents in and copy its share link. Then submit  /set_gdrive_folder YOUR_SHARE_LINK command in chat You only need to do this once per session.
2. Set a title, if desired. Use /set_document_title YOUR_TITLE in chat to set the title. Spaces are fine, and no need to quote. This title will be used as the file name and document title of all subsequent uploads until a new title is set.
3. Generate the document. /make_docx or something like ‘@bartleby save that output to gdrive’ will upload the last message in chat. Or if you want to capture an earlier message, right click on it and select ‘apps’ > ‘Save to gdrive’ from the context menu.

## 4. Command reference

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

Bartleby is easily extensible to new models and should work out-of-the-box with any Mistral or Falcon family models available via HuggingFace - especially those which come with a chat template.
