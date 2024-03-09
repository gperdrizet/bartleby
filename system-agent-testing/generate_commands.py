import os
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM

# Set HuggingFace cache
os.environ['HF_HOME'] = '/mnt/fast_scratch/huggingface_transformers_cache'

if __name__ == '__main__':

    # Give torch some CPU
    torch.set_num_threads(8)
    
    # Initialize the model and tokenizer
    tokenizer=AutoTokenizer.from_pretrained('tiiuae/falcon-7b-instruct')
    model=AutoModelForCausalLM.from_pretrained('tiiuae/falcon-7b-instruct', device_map='cpu')

    # Read the human-written natural language command examples into a dataframe 
    input_file='./human_NL_commands.4.csv'
    human_commands_df = pd.read_csv(input_file, keep_default_na=False)
    print(human_commands_df.head())

    # Empty list to store human and synthetic commands, used to check for duplicates
    # before adding a new command to output
    commands = []

    # Empty list to store output dicts
    output_commands = []

    # Loop on rows of human NL command examples dataframe
    for index, row in human_commands_df.iterrows():
        print(f"\nInput command: {row['command']}")

        # If we don't have it already, add the natural language command to the output
        if row['command'] not in commands:

            # Add this command to the simple list of those we have seen
            commands.append(row['command'])

            # Format this command as a dict and add to output
            command_dict = {
                'summary': row['action'], # The 'summary' is the is the specific action phrase we want the agent to produce
                'text': row['command'] # The text is the natural language command
            }

            # Add the formatted command to the list of outputs
            output_commands.append(command_dict)

        # Format command with prompt for input to the model
        input_string=f"Rewrite the following statement while preserving the meaning: {row['command']}"
        
        # Tokenize the input
        input_ids=tokenizer(input_string, return_tensors='pt')

        # Generate
        output_ids=model.generate(
            **input_ids, 
            temperature=1.0,
            num_beams=20, 
            num_beam_groups=20, 
            max_new_tokens=128, 
            diversity_penalty=0.5,
            num_return_sequences=10,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id
        )

        # Un-tokenize
        replies=tokenizer.batch_decode(output_ids, eos_token_id=tokenizer.eos_token_id)

        # Collect and save responses
        for reply in replies:
            reply=reply.split('\n')
            reply=reply[-1]
            reply=reply.replace('<|endoftext|>', '')
            print(f'Output: {reply}')

            # Check to see if we already have this one
            if reply not in commands:

                commands.append(reply)

                # Format it as a dict and add to output
                command_dict = {
                    'summary': row['action'], # The 'summary' is the is the specific phrase we want the agent to produce
                    'text': reply # The text is the generated natural language command
                }

                output_commands.append(command_dict)

        # Save result
        output_commands_df = pd.DataFrame(output_commands)
        output_commands_df.to_csv(
            'NL_commands_dataset.4.csv',
            header=True,
            index=False
        )
