import bartleby.configuration as conf

def run():

    for replicate in range(1, conf.replicates + 1):
        print(f'\nReplicate: {replicate}')

        for repetition in range(1, conf.repetitions + 1):
            print(f' Repetition: {repetition}')

    print()