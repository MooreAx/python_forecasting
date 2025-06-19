#class for generic parts

class Part:
    def __init__(self, name, format, brand, description, size, pstatus,
                 launch_cutoff, exit_cutoff):
        self.name = name
        self.format = format
        self.brand = brand
        self.description = description
        self.size = size
        self.pstatus = pstatus
        self.launch_cutoff = launch_cutoff #product availability
        self.exit_cutoff = exit_cutoff #hard kill date
        
        #not yet defined
        self.listings = []
        #use composition so that listings have parts. but i also want to be able to refer
        #back to the part within a lisitng... for example, to access properites of other listings
        #for the same part. not sure how to do this yet.

    @property
    def first_ship_date(self):
        #returns first ship date across listing
        pass
    
    @property
    def first_ship_prov(self):
        #returns first ship prvince
        pass




