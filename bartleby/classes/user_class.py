import bartleby.configuration as conf

class User:
    '''Class to hold data specific to a user'''

    def __init__(self, user_name):
        '''Creates empty data structure for user's conversation with
        bartleby and reads some defaults from configuration file on
        instantiation a new user.'''

        # Set name
        self.user_name = user_name

        # New user defaults
        self.initial_prompt = conf.initial_prompt
        self.model_type = conf.default_model_type
        self.gdrive_folder_id = None
        self.document_title = conf.default_title
        
        # Start messages list with default prompt
        self.messages = [{'role': 'system', 'content': self.initial_prompt}]

        # Set default generation mode from config file
        self.generation_mode = conf.default_generation_mode

        # Empty dict. to hold model generation configurations
        self.generation_configurations = {}

        # N most recent messages to include when prompting the model
        self.model_input_buffer_size = conf.model_input_buffer_size

    def set_generation_mode(self):

        for key, value in conf.generation_mode[self.generation_mode].items():
            setattr(self.generation_configurations[self.model_type], key, value)

    def restart_conversation(self):
        
        # Start messages list with default prompt
        self.messages = [{'role': 'system', 'content': self.initial_prompt}]


#############################################################################79