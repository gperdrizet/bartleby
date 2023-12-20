import bartleby.configuration as conf
import bartleby.llm_class as llm

def run():

    # Initialize the model, tokenizer and generation configuration.
    llm_instance = llm.Llm()
    llm_instance.initialize_model()
    llm_instance.initialize_model_config()
    print('Model initialized successfully\n')

    # Loop on replicates
    for replicate in range(1, conf.replicates + 1):
        print(f'\nReplicate: {replicate}')

        # If this is not the first, replicate delete and re-initialize the model, clear memory
        if replicate > 1:
            llm_instance.restart_model()
            print(f'Model cleared and restarted')

        # Do the repetitions
        for repetition in range(1, conf.repetitions + 1):
            print(f' Repetition: {repetition}')

            # Format query as dict
            user_message = {
                'role': 'user', 
                'content': conf.query
            }

            # Add new message to conversation
            llm_instance.messages.append(user_message)

            # Tokenize the updated conversation
            prompt = llm_instance.tokenizer.apply_chat_template(
                llm_instance.messages, 
                tokenize = True, 
                add_generation_prompt = True,
                return_tensors = 'pt'
            ).to('cuda')

            print(f' Model input {type(prompt)}: {prompt.size()}')

            # Generate response
            output_ids = llm_instance.model.generate(
                prompt, 
                generation_config = llm_instance.gen_cfg
            )

            print(f' Model output {type(output_ids)}: {output_ids.size()}\n')

            # Un-tokenize response
            model_output = llm_instance.tokenizer.batch_decode(
                output_ids, 
                skip_special_tokens = True, 
                clean_up_tokenization_spaces = False
            )

            model_output_content = model_output[0]

            reply = model_output_content.split('\n<|assistant|>\n')[-1]

            model_message = {
                'role': 'assistant',
                'content': reply
            }
            
            llm_instance.messages.append(model_message)

    print()