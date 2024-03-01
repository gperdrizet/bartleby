import bartleby.configuration as conf

class Matrix:
    '''Class to hold data specific to a user'''

    def __init__(self, user_name):
        '''Creates empty data structure for user's conversation with
        bartleby and reads some defaults from configuration file on
        instantiation a new user.'''

        # Set name
        self.user_name = user_name

        # New user defaults
        self.initial_prompt = conf.initial_prompt
        self.model_type = conf.model_type
        self.gdrive_folder_id = conf.gdrive_folder_id
        self.document_title = conf.default_title
        
        # Start messages list with default prompt
        self.messages = [{'role': 'system', 'content': self.initial_prompt}]

#############################################################################79