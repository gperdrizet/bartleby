# Project architecture

## 1. Planned

```text
        +--------------+         +--------------+
        |              |         |              |
        |     LLM      |         | Google Docs  |
        |              |         |              |
        +--------------+         +--------------+
                |                       |
                |                       |
                |                       |                       
        ######################################### 
        #                                       #
        #             Communicator              #
        #                                       #
        ######################################### 
            |               |               |
            |               |               |
            |               |               |
+---------------+   +---------------+   +--------------+
|               |   |               |   |              |
|    Matrix     |   |    Discord    |   |     Shell    |
|               |   |               |   |              |
+---------------+   +---------------+   +--------------+
```

## 2. Current

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
