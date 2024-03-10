import torch

def prompt_mistral(input_messages, device_map, model, tokenizer, generation_configuration):

    # Tokenize the updated conversation
    prompt = tokenizer.apply_chat_template(
        input_messages,
        tokenize = True,
        add_generation_prompt = True,
        return_tensors = 'pt'
    )
    
    # Select device
    if device_map != 'cpu':
        prompt=prompt.to('cuda')

    # Generate response
    output_ids = model.generate(
        prompt,
        generation_config = generation_configuration
    )

    # Un-tokenize response
    model_output = tokenizer.batch_decode(
        output_ids,
        skip_special_tokens = True,
        clean_up_tokenization_spaces = False
    )

    # Get number of tokens generated for logging
    num_tokens_generated = output_ids.size()[1] - prompt.size()[1]

    # Parse model's response
    model_output_content = model_output[0]
    reply = model_output_content.split('\n<|assistant|>\n')[-1]

    return reply, num_tokens_generated

def prompt_falcon(input_messages, model, tokenizer, generation_configuration):

    # Empty list to hold parsed and formatted messages
    messages = []

    # Format messages for input to falcon
    for message in input_messages:
        
        if message['role'] == 'system': 
            messages.append(f"system: {message['content']}")

        elif message['role'] == 'user': 
            messages.append(f"user: {message['content']}")

        elif message['role'] == 'assistant': 
            messages.append(f"assistant: {message['content']}")

    # Add a final 'assistant:' line with no message to prompt reply from model
    messages.append('assistant:')

    # Collect messages from list into string
    input = '\n'.join(messages)

    # Tokenize the input messages
    inputs = tokenizer(input, return_tensors='pt')

    # Generate the response
    output_ids = model.generate(
        **inputs, 
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        generation_config = generation_configuration,
        num_return_sequences = 1
    )

    # Get total number of tokens generated for logging
    num_tokens_generated = output_ids.size()[1]

    # Un-tokenize the response
    reply = tokenizer.batch_decode(output_ids, eos_token_id=tokenizer.eos_token_id)

    # Fence to catch index errors in reply parse caused by empty response
    try:
        # Parse the reply
        reply = reply[0]
        reply = reply.split('\n')
        reply = reply[len(input_messages)]
        reply = reply.replace('assistant: ', '')

    except IndexError as e:
        reply = ''

    return reply, num_tokens_generated

def prompt_dialo(input_messages, model, tokenizer):
    # Collect and encode chat history

    # Empty holder for tokenized messages
    tokenized_messages = []

    # Add end-of-sequence as last 'message' in input
    input_messages.append({'content': tokenizer.eos_token})

    # Tokenize the messages
    for message in input_messages:
        tokenized_message = tokenizer.encode(message['content'], return_tensors='pt')
        tokenized_messages.append(tokenized_message)

    # Concatenate tokenized chat messages
    inputs = torch.cat(tokenized_messages, dim=-1)

    # Generate response
    output_ids = model.generate(inputs, max_length=1000, pad_token_id=tokenizer.eos_token_id)

    # Get total number of tokens generated for logging
    num_tokens_generated = len(output_ids[:, inputs.shape[-1]:][0])

    # Un-tokenize last response by bot
    reply = tokenizer.decode(output_ids[:, inputs.shape[-1]:][0], skip_special_tokens=True)

    return reply, num_tokens_generated