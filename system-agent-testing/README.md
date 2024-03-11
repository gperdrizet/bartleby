# System Agent

## 1. Introduction

Plan is to build simple agent functionality into bartleby for use with system commands. The goal is to give the end user natural language control over bartleby's functions rather than forcing them to use a specific parameter/argument command.

To accomplish this, a text summarization model will be fine-tuned to map 'commands' in the form of natural language questions or statements onto function names and arguments to bartleby's system command logic. Some examples:

| user input                                             | bartleby's action                       |
|--------------------------------------------------------|-----------------------------------------|
| Hay bartleby, let's restart the conversation!          | user.restart_conversation()             |
| Clear the chat history please.                         | user.restart_conversation()             |
| Save your last response to gdrive for me.              | docx_instance.generate(user, 1)         |
| Here's the link to our shared gdrive: drive.google.com | user.gdrive_folder_id='drive.google.com |

Here are a couple of things to consider:

1. Actions can be grouped into two types - those that take an argument vs those that don't. The latter will probably be easier to implement.
2. There are a small number of possible actions.
3. The agent does not have to generate the exact command to execute the action, it just needs to generate stereotyped, parsable output from which we can tell what the user wants to do.
4. The model doing the chatting and text generation does not need to be the agent model.
5. Leaving the parameter/argument style commands in place gives a fallback option if the agent fails.
6. A LLM can be used to generate training inputs from a few human written examples, i.e. 'Rephrase the following statement: Clear the chat history please.' etc.

Think of it this way - all we need to do is translate a natural language commands into pre-defined command flags and the system will work.

## 2. The plan

In order to make this tractable and test it quickly with the greatest possibility of success, we will start with a small summarization model and just a few commands which do not need arguments. The goal is to implement the following:

1. Fine-tuned system-agent model monitors the chat for suspected user commands.
2. When a message that is likely to be a command is encountered, the system agent picks a command to be executed.
3. If a message that might be a command is encountered, prompt the user to rephrase or ask them to confirm what they are trying to do.
4. If any kind of failure or error occurs, the system prompts the user to use the parameter/argument syntax.

Here are the steps to get there:

1. Pick a few argument-less commands and write some natural language examples of each.
2. Use an LLM to generate as many rephrased versions of the human written natural language commands as possible.
3. Curate the generated natural language commands.
4. Fine tune an LLM with natural language command - action pairs.
5. Test
6. Repeat

Questions that need answers:

1. What LLM do we use to generate re-phrased versions of human written natural language commands?
2. What LLM do we fine tune on our mixed human/synthetic natural language commands dataset?
3. What/how many commands do we start with?
4. How do we get/quantify the probability that a given user message is requesting a given action?

## 3. Models

For generation of re-phrased natural language commands from human written examples, let's use falcon-7B-instruct. We already have this model cached and running and know how to prompt it. Also, it's an instruct model so it may do better with prompts like 'Rephrase the following statement:' than pure chat models.

For the agent, let's start with T5-small. It's easy to fine tune and does an OK job of summarization. Hopefully this will be a slow-ball for it.

Last, let's pick some actions and write natural language commands for them. Also, thinking we should include a set of non-command messages labeled as 'none' or 'not a command' or something similar. Here are some examples:

| Command                                       | Action       |
|-----------------------------------------------|--------------|
| Please reset this chat.                       | restart chat |
| Clear the message history.                    | restart chat |
| Start a fresh conversation.                   | restart chat |
| Generate document and upload.                 | make docx    |
| Create gdrive file.                           | make docx    |
| Save the last message.                        | make docx    |
| Do you know a good recipe for scrambled eggs? | None         |
| Can you tell me a joke?                       | None         |
| What is your favorite color?                  | None         |

Then, we'll just fine-tune the heck out of it until it converges on something and see how it does picking out request to restart the chat vs make a document on gdrive vs regular chat interactions. Should be pretty immediately obvious if it works or not.

## 4. Testing

It works great! I guess I'm not surprised, but this is a very cool feature. It *feels* next gen, but is very easy to do in house. We don't need an external API or a big clever model or anything like that. This is just an easy to train translation task.

OK, let's add a bunch more commands. This is all going to be done with throw-away scripts, so let's take some notes so we don't end up repeating work we already did.

## 5. Commands added

| Human inputs            | Augmented dataset         | Actions                              |
|-------------------------|---------------------------|--------------------------------------|
| human_NL_commands.1.csv | NL_commands_dataset.1.csv | --restart-chat                       |
|                         |                           | --make-docx                          |
|                         |                           | None                                 |
| human_NL_commands.2.csv | NL_commands_dataset.2.csv | --show-prompt                        |
|                         |                           | --update-config max_new_tokens VALUE |
|                         |                           | --update-config temperature VALUE    |
| human_NL_commands.3.csv | NL_commands_dataset.3.csv | --commands                           |
|                         |                           | --input-buffer-size                  |
|                         |                           | --show-config                        |
| human_NL_commands.4.csv | NL_commands_dataset.4.csv | --update-input-buffer N              |
|                         |                           | --set-document-title                 |
|                         |                           | --set-gdrive-folder FOLDER           |

As we write and augment examples for more commands, they are concatenated manually after curation into *NL_commands_dataset.complete.csv* for use in fine-tuning.

**Note:** Thinking we should probably add a lot more None or no command examples as the number of commands we are trying to encode increases.

**Also note:** It might not be a bad idea to separate the commands which take a numerical argument from those that don't and fine-tune two system-agent models separately, one specialized in each command type.

**Other notes:**

1. When setting the title, the synthetic command generation seems to struggle with examples where the new title is not capitalized of in quotes.

## 6. Commands left to add

```text
--update-prompt PROMPT          Updates the system prompt to PROMPT and restarts chat history.
--show-config-value PARAMETER   Show the value of generation configuration PARAMETER.
--update-config PARAMETER VALUE Updates generation configuration PARAMETER to VALUE.
--supported-models              Post supported models to chat.
--swap-model MODEL              Change the model type used for generation.
--document-title                Posts current Google Doc document title to chat.
--make-docx N                   Makes and uploads docx document to Google Drive where N is the
                                reverse index in chat history, e.g. 1 is the last message, 2
                                the second to last etc. If N is omitted, defaults to last message.
```

## 7. Testing notes

1. Updating the model input buffer size chokes, not sure where - seemed like it was working in testing.
2. Looks like out fine tuned T5 started getting confused between the 3rd and 4th sets of new commands It's having trouble differentiating between input buffer and max output token updates.

I think we really need to see a probability distribution over the top many commands the agent thinks the user's message means. For example, 'complete the statement: the early bird' makes it reset the chat logs, hahaha. I have to laugh at that one.

Ok, so maybe we just found the limit of T5-small's ability to do this type of thing. We didn't test the model with 12 commands encoded but we did test it with 9 and it seemed to work great. Two thoughts here:

1. There's a clear limit to doing it this way - it's not scalable. Each specific action needs a human to come up with example commands, then curate synthetic examples of the same and then somebody needs to write a parse stanza to catch the agent's output and run it.

2. It's not really general - i.e. the interaction between the user and agent must follow a rigid structure. For example, asking: 'How do I change x' and then saying: 'OK, change it to y' wouldn't work. And the user cannot just talk naturally with the agent about what commands are available and what they do.
