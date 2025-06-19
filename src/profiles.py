# class for profiles


class Profile_Definition:
    #stores profile definitions
    def __init__(self, name, definition):
        self.name = name
        self.definition = definition

class Profile:
    #applies a profile definition to a particular forecast item
    def __init__(self, profile_definition, anchor_date, loop=False):
        self.profile_definition = profile_definition
        self.anchor_date = anchor_date,
        self.loop = loop