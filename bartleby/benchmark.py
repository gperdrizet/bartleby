import os
import time
import torch
import tracemalloc
import pandas as pd
import bartleby.configuration as conf
import bartleby.llm_class as llm

class Results():
    '''Class to hold objects and methods for
    collection of results'''

    def __init__(self, results_dir, collection_vars):

        # Output file for results
        self.output_file = f'{results_dir}/benchmarking_results.csv'

        # Create dict for data
        self.data = {}

        # Empty list to data dict for each collection var
        for collection_var in collection_vars:
            self.data[collection_var] = []

    def save(self, overwrite: bool = False) -> None:

        # Make dataframe of new results
        results_df = pd.DataFrame(self.data)

        if overwrite == False:

            # Read existing results if any and concatenate new results
            if os.path.exists(self.output_file):
                old_results_df = pd.read_csv(self.output_file)
                results_df = pd.concat([old_results_df, results_df])

        # Save results for run to csv
        results_df.to_csv(self.output_file, index = False)

def run():

    # Create instance of results class to collect data
    collection_vars = [
        'replicate',
        'repetition',
        'input tokens',
        'output tokens',
        'generated tokens',
        'total generation time (sec.)',
        'generation rate (tokens/sec.)',
        'model GPU memory footprint (GB)',
        'peak GPU memory (GB)',
        'data GPU memory footprint (GB)'
        'peak GPU system memory (GB)'
    ]
    results = Results(
        results_dir=conf.DATA_PATH,
        collection_vars=collection_vars
    )

    # Initialize the model, tokenizer and generation configuration.
    llm_instance = llm.Llm()
    llm_instance.initialize_model()
    llm_instance.initialize_model_config()
    print('Model initialized successfully\n')

    # Loop on replicates
    for replicate in range(1, conf.replicates + 1):
        print(f'Replicate: {replicate}')

        # Do the repetitions
        for repetition in range(1, conf.repetitions + 1):
            print(f' Repetition: {repetition}')

            # Format query as dict
            message = {
                'role': 'user', 
                'content': conf.query
            }

            # Add new message to conversation
            llm_instance.messages.append(message)

            # Start memory trace
            tracemalloc.start()

            # Start generation timer
            generation_start_time = time.time()

            # Tokenize the updated conversation
            prompt = llm_instance.tokenizer.apply_chat_template(
                llm_instance.messages, 
                tokenize = True, 
                add_generation_prompt = True,
                return_tensors = 'pt'
            ).to('cuda')

            # Generate response
            output_ids = llm_instance.model.generate(
                prompt, 
                generation_config = llm_instance.gen_cfg
            )

            # Un-tokenize response
            model_output = llm_instance.tokenizer.batch_decode(
                output_ids, 
                skip_special_tokens = True, 
                clean_up_tokenization_spaces = False
            )

            # Stop the generation timer
            generation_end_time = time.time()

            # Stop memory trace and collect results
            system_memory, peak_system_memory = tracemalloc.get_traced_memory()
            peak_system_memory = peak_system_memory * 1024
            tracemalloc.stop()

            # Get models reply string
            model_output_content = model_output[0]
            reply = model_output_content.split('\n<|assistant|>\n')[-1]

            # Format model reply as dict
            model_message = {
                'role': 'assistant',
                'content': reply
            }
            
            # Add reply to conversation for the next repetition
            llm_instance.messages.append(model_message)

            # Collect data from this repetition
            generation_dT = generation_end_time - generation_start_time

            input_tokens = prompt.size(1)
            output_tokens = output_ids.size(1)
            generated_tokens = output_tokens - input_tokens

            generation_rate = generated_tokens / generation_dT

            peak_GPU_memory = 0

            for i in range(4):
                peak_GPU_memory += torch.cuda.max_memory_allocated(i) / 1024**3

            model_GPU_memory_footprint = llm_instance.model.get_memory_footprint() / 1024**3
            data_GPU_memory_footprint = peak_GPU_memory - model_GPU_memory_footprint

            results.data['replicate'].append(replicate)
            results.data['repetition'].append(repetition)
            results.data['input tokens'].append(input_tokens)
            results.data['output tokens'].append(output_tokens)
            results.data['generated tokens'].append(generated_tokens)
            results.data['total generation time (sec.)'].append(generation_dT)
            results.data['generation rate (tokens/sec.)'].append(generation_rate)
            results.data['model GPU memory footprint (GB)'].append(model_GPU_memory_footprint)
            results.data['peak GPU memory (GB)'].append(peak_GPU_memory)
            results.data['data GPU memory footprint (GB)'].append(data_GPU_memory_footprint)
            results.data['peak system memory'].append(peak_system_memory)

            # Save the results from this repetition
            results.save(overwrite=True)

        # Delete and re-initialize the model and tokenizer, clear memory
        llm_instance.restart_model()
        print(f'Model cleared and restarted')

    print()