import pandas as pd
from itertools import islice
from read_config import listing_dict

#for key, listing in islice(listing_dict.items(), 100):
for key, listing in listing_dict.items():
    listing.calculate_baseline()
    listing.generate_forecast()
    listing.apply_profile()