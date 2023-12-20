import argparse
from bartleby import bartleby
from bartleby import benchmark


if __name__ == "__main__":

    arguments = [
        ['--benchmark', 'Run performance benchmark instead of starting chatbot.']
    ]

    # Instantiate command line argument parser
    parser = argparse.ArgumentParser(
        prog = 'bartleby.py',
        description = 'Bartleby the LLM writing assistant.',
        epilog = 'Bottom text'
    )
    
    # Add arguments
    for argument in arguments:

        parser.add_argument(
            argument[0], 
            choices=[str(True), str(False)], 
            default=str(False), 
            help=argument[1]
        )

    # Parse the arguments
    args = parser.parse_args()

    if args.benchmark == 'True':
        benchmark.run()

    elif args.benchmark == 'False':
        bartleby.run()