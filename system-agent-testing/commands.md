# Bartleby system command manual

## 1. Overview of all available commands

| chat command                 | discord slash command         | system agent command | action                                                                                  |
|------------------------------|-------------------------------|----------------------|-----------------------------------------------------------------------------------------|
| --commands                   | None                          | Yes                  | Posts list of available chat commands                                                   |
| --input-buffer-size          | /show_input_buffer_size       | Yes                  | Posts the number of most recent chat messages currently being used as input the the LLM |
| --update-input-buffer-size N | /update_input_buffer_size N   | Yes                  | Sets the number of most recent chat messages to use as input for the LLM to N           |
| --show-input-messages        | None                          | No                   | Posts the current contents of the LLM input buffer in chat                              |
| --show-prompt                | /show_prompt                  | Yes                  | Posts the current initial system prompt used to start each conversation                 |
| --update-prompt PROMPT       | /update_prompt PROMPT         | No                   | Sets initial system prompt used to start new conversations to PROMPT                    |
| --restart-chat               | /reset_chat                   | Yes                  | Clears message history and starts a new conversation                                    |
| --show-generation-mode       | /show_generation_mode         | No                   | Post the current generation decoding mode to chat                                       |
| --show-generation-modes      | /show_generation_modes        | No                   | Posts the list of available generation mode presets to chat                             |
| --set-generation-mode MODE   | /update_generation_mode MODE  | No                   | Sets generation mode to MODE where mode is one of the available presets                 |
| --show-config                | /show_generation_config       | Yes                  | Posts any values from transformers.GenerationConfig not currently set to model defaults |
| --show-config-full           | /show_generation_config_full  | No                   | Posts all values from transformers.GenerationConfig                                     |
| --update-config X Y          | /update_generation_config X Y | No (except temp. and max new tokens) | Updates the value of any parameter X from transformers.GenerationConfig to Y |
| None                         | /show_generation_config_value X | No                 | Posts the current value of transformers.GenerationConfig parameter X to chat            |
| --supported-models           | /show_supported_models        | Yes                  | Post the list of available models to chat                                               |
| None                         | /show_current_model           | No                   | Post the name of the model currently being used for generation                          |
| --swap-model MODEL           | /swap_model MODEL             | Yes                  | Changes the LLM being used for response generation to MODEL from supported model list   |
| --document-title             | /show_document_title          | Yes                  | Posts the current document title, used for saving output to gdrive, in chat             |
| --set-document-title TITLE   | /set_document_title TITLE     | Yes                  | Sets the document title that will be used to save output to gdrive                      |
| --set-gdrive-folder LINK     | /set_gdrive_folder LINK       | Yes                  | Sets the target gdrive folder used for document uploads to LINK where link is a google drive folder share link |
| --make-docx N                | /make_docx (no argument)      | Yes                  | Makes a docx file using document title for title and filename, uploads it to gdrive using a previously provided share link. Chat command takes integer N specifying how many most recent messages to include, discord slash command takes no arguments and generates document from the most recent message. |

OK, cool - I think that's all of the commands we have right now. Discord has one additional - you can save a message as docx on gdrive via a right click context menu on that message. Pretty happy with what we have, one possible addition would be the response length penalty in the generation configuration. It takes a tuple so I think if a user tried to set it with --update-config we would probably choke. Maybe we should separate that one out. We could also just choose not to expose it because we are going to set it dynamically via our system agent. Other than that, we are definitely done adding things. Priority now is to get this organized and make the command naming consistent. I think the first thing to do is break the commands up into groups for the documentation.

## 2. Command groups

### 2.1. System commands

| chat command                 | discord slash command         | system agent command | action                                                                                  |
|------------------------------|-------------------------------|----------------------|-----------------------------------------------------------------------------------------|
| --commands                   | None                          | Yes                  | Posts list of available chat commands                                                   |
| --input-buffer-size          | /show_input_buffer_size       | Yes                  | Posts the number of most recent chat messages currently being used as input the the LLM |
| --update-input-buffer-size N | /update_input_buffer_size N   | Yes                  | Sets the number of most recent chat messages to use as input for the LLM to N           |
| --show-input-messages        | None                          | No                   | Posts the current contents of the LLM input buffer in chat                              |
| --show-prompt                | /show_prompt                  | Yes                  | Posts the current initial system prompt used to start each conversation                 |
| --update-prompt PROMPT       | /update_prompt PROMPT         | No                   | Sets initial system prompt used to start new conversations to PROMPT                    |
| --restart-chat               | /reset_chat                   | Yes                  | Clears message history and starts a new conversation                                    |

First decision to make here is if/what verbs to use, i.e. show_input_buffer_size vs --input-buffer-size. Also, I think we should add the '--commands' to the system agent. I think that's a pretty useful one to have at the user's fingertips.

### 2.2. Generation configuration commands

| chat command                 | discord slash command         | system agent command | action                                                                                  |
|------------------------------|-------------------------------|----------------------|-----------------------------------------------------------------------------------------|
| --show-generation-mode       | /show_generation_mode         | No                   | Post the current generation decoding mode to chat                                       |
| --show-generation-modes      | /show_generation_modes        | No                   | Posts the list of available generation mode presets to chat                             |
| --set-generation-mode MODE   | /update_generation_mode MODE  | No                   | Sets generation mode to MODE where mode is one of the available presets                 |
| --show-config                | /show_generation_config       | Yes                  | Posts any values from transformers.GenerationConfig not currently set to model defaults |
| --show-config-full           | /show_generation_config_full  | No                   | Posts all values from transformers.GenerationConfig                                     |
| --update-config X Y          | /update_generation_config X Y | No (except temp. and max new tokens) | Updates the value of any parameter X from transformers.GenerationConfig to Y |
| None                         | /show_generation_config_value X | No                 | Posts the current value of transformers.GenerationConfig parameter X to chat            |
| --supported-models           | /show_supported_models        | Yes                  | Post the list of available models to chat                                               |
| None                         | /show_current_model           | No                   | Post the name of the model currently being used for generation                          |
| --swap-model MODEL           | /swap_model MODEL             | Yes                  | Changes the LLM being used for response generation to MODEL from supported model list   |

Same comment here about if/when to use verbs consistently. Thinking we should not use 'show' and only use 'set' rather than 'update'. This way many commands will come in pairs, e.g. '--generation-config' to list the generation config and '--set-generation-config' to make a change. Also, I think we can loose 'show_generation_config_value'.

### 2.3. Document commands

| chat command                 | discord slash command         | system agent command | action                                                                                  |
|------------------------------|-------------------------------|----------------------|-----------------------------------------------------------------------------------------|
| --document-title             | /show_document_title          | Yes                  | Posts the current document title, used for saving output to gdrive, in chat             |
| --set-document-title TITLE   | /set_document_title TITLE     | Yes                  | Sets the document title that will be used to save output to gdrive                      |
| --set-gdrive-folder LINK     | /set_gdrive_folder LINK       | Yes                  | Sets the target gdrive folder used for document uploads to LINK where link is a google drive folder share link |
| --make-docx N                | /make_docx (no argument)      | Yes                  | Makes a docx file using document title for title and filename, uploads it to gdrive using a previously provided share link. Chat command takes integer N specifying how many most recent messages to include, discord slash command takes no arguments and generates document from the most recent message. |

Need to decide what the behavior of make-docx should be - does it just use the last message, or do we take a range while defaulting the the last message if no range is given? I the latter is better, gives flexibility along with ability not to use it.

OK, I think we are good-to-go. Let's make a final list here and update with changes as we are making them, so we don't get confused