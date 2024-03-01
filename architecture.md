# Project architecture

## 1. Current Set-up

```text
+----------------------------+      +-------------------+
|            LLM             |      |    Google Docs    |
|----------------------------|      |-------------------|
| llm_class.py               |      | docx_class.py     |
|                            |      |                   |
| .initialize_model()        |      | .async_generate() |
| .add_conversation()        |      | .generate()       |
| .restart_model()           |      | .load_template()  |
| .initialize_model_config() |      | .upload()         |
| .prompt_model()            |      +-------------------+
+----------------------------+              |
                |                           |
                |                           |
                |                           |                       
        ######################################### 
        #             Communicator              #
        ######################################### 
        # bartleby.py                           #
        #                                       #
        # .run()                                #
        # .main_local_text_loop()               #
        # .main_matrix_loop()                   #
        ######################################### 
            |                               |
            |                               |
            |                               |
+--------------------------+          +--------------+
|          Matrix          |          |    Shell     |
|--------------------------|          +--------------+
| matrix_class.py          |
|                          |
| .start_matrix_client()   | 
| .post_message()          |
| .catch_message()         |
| .parse_command_message() |
+--------------------------+ 


 +------------------+       +--------------------------+
 | configuration.py |       | helper_functions.py      |
 +------------------+       |                          |
                            | .parse_command_message() |
                            +--------------------------+
```

OK, good news is that we have the bones and everything already works. But, this thing in badly in need of a major re-organization to support the two main features that we are trying to add:

1. Multiple users
2. Discord

Better modularity and separation of function is needed. For example: .add_conversation() shouldn't be in the llm_class because it's specific to a user, not the LLM instance. Another example would be the .parse_command_message() method in the matrix class. It handles both catching the command from the user and executing it. This should be separated such that the matrix class catches commands from conversations on matrix and then sends them on to a command executor somewhere (e.g. in the llm class) which can also take input from discord or the shell.

Since multi-user support already works, this is the perfect time to clean up and modularize everything. The effort spent there will pay off when adding Discord support and containerizing for deployment.

## 3. Brainstorming

### 3.1. LLM vs user

First thing to divide up is what belongs with the llm instance and what belongs to a specific user. Since there will be multiple users talking to the same llm, some parameters will be specific to the llm and common to all of the users and others will be specific to each user. **Note**: As the feature set gets more advances, this might actually become the heart of bartleby, for example what if we have two users who want to talk to different models? In that case the user configurations are dictating how/when llm instances need to be initiated.

| parameter      | initial value    | ownership |
|----------------|------------------|-----------|
| model_type     | configuration.py |   LLM&dagger;    |
| initial_prompt | configuration.py |   user    |
| device_map     | configuration.py |   LLM     |
| CPU_threads    | configuration.py |   LLM     |
| gen_cfg        | model.config     |   user    |

**&dagger;** An llm instance owns it's model type in the sense that it cannot be changed. If a user wants to switch model types, a new llm instance needs to be spun up.

### 3.2. Other parameters that belong to the user

| parameter           | initial value               |
|---------------------|-----------------------------|
| run_mode            | set by arrival of message?  |
| room/server details | not sure&dagger;            |
| document_title      | configuration.py            |
| gdrive details      | see room/server_details     |
| input_buffer_size   | configuration.py            |

**&dagger;** This one deserves some thought - it needs to come from onboarding somehow and will depend on which communication method the user registers: Matrix or Discord. It needs to be stored securely somewhere so that when bartleby fires up he can login and listen to all the right rooms/servers.

Another possibility is to say forget it - and make one matrix room/space and one discord server where bartleby lives and anyone who wants to talk to him has to log in there. This approach would be much simpler but not nearly as cool as being able to add him to whatever space you want.

Google drive is also a lot of complexity and maybe a big ask for a new user - i.e. please authorize this weird AI chatbot thing to mess with your google drive.

Let's stash the login concerns for now, we can just go around them if we run out of time to implement them well. Focus on rewiring bartleby to monitor chat services and catch user messages from them first, then decide what to do in response to the message. Seems like there are two (or three) possibilities:

1. Start an llm instance
2. Prompt an llm instance
3. Interact with Google Drive

## 4. Version 2 Set-up

After some heavy rewiring inspired by the above brainstorming discussion and re-writing almost everything here is the new architecture:

```text
+----------------------------+
|            LLM             |
|----------------------------|
| llm_class.py               | 
|                            |
| .initialize_model()        |
| .restart_model()           |
| .prompt_model()            |
+----------------------------+ 
                |
                |
                |
        #########################################
        #             Communicator              #
        #########################################       +--------------------------+ 
        # bartleby.py                           #       |          User            | 
        #                                       #-------|--------------------------| 
        # .run()                                #       | user_class.py            |
        # .main_matrix_loop()                   #       +--------------------------+ 
        ######################################### 
            | 
            |
            | 
+--------------------------+ 
|          Matrix          | 
|--------------------------| 
| matrix_class.py          |
|                          |
| .start_matrix_client()   | 
| .post_message()          |
| .post_system_message()   |
| .catch_message()         |
| .parse_command_message() |
+--------------------------+ 


 +------------------+       +--------------------------+
 | configuration.py |       | helper_functions.py      |
 +------------------+       |                          |
                            | .parse_command_message() |
                            | .start_logger()          |
                            +--------------------------+
```
