# read forecast configuration file

import pandas as pd
import janitor as jn

from parts import Part
from listings import Listing
from read_tables import df_depletions, df_shipments, df_first_last_ship

#takes grouped DataFrame and turns it into a dictionary of DataFrames keyed by (part, prov).
shipments_dict = dict(tuple(df_shipments.groupby(['part', 'prov'])))
firstlastship_dict = dict(tuple(df_first_last_ship.groupby(['part', 'prov'])))
depletions_dict = dict(tuple(df_depletions.groupby(['part', 'prov'])))

#load excel file
config_file = pd.ExcelFile('config/forecast_configuration.xlsx')

#read sheets into data frames
df_products = config_file.parse('Products').clean_names()
df_products['part'] = df_products['part'].astype(str)

df_listings = config_file.parse('Listings').clean_names()
df_listings['part'] = df_listings['part'].astype(str)

#don't clean names on the profiles or they won't mach
df_seasonality = config_file.parse('Seasonality')
df_lifecycle = config_file.parse('Lifecycle')
df_promotion = config_file.parse('Promotion')

print(df_seasonality.head(20))


#function to extract the relevant profile columns. if it doesn't exist, return None
def extract_profile(df, name):
    try:
        profile = df[['Week', name]]
    except:
        profile = None
    return profile

#instantiate products

product_dict = {}

for _, row in df_products.iterrows():
    product = Part(
        name = row['part'],
        format = row['format'],
        brand = row['brand'],
        description = row['description'],
        size = row['size'],
        pstatus = row['p_status'],
        launch_cutoff = row['launchcutoff'],
        exit_cutoff = row['exitcutoff'],
    )
    #add product to dictionary with SKU as key
    product_dict[row['part']] = product

print(len(product_dict), "products loaded.")

#instantiate listings

listing_dict = {}

for _, row in df_listings.iterrows():

    depletions = depletions_dict.get((row['part'], row['prov']), pd.DataFrame())
    shipments = shipments_dict.get((row['part'], row['prov']), pd.DataFrame())
    firstlastship = firstlastship_dict.get((row['part'], row['prov']), None) # a dataframe
    first_ship = firstlastship.iloc[0]['first_ship'] if firstlastship is not None else None
    last_ship = firstlastship.iloc[0]['last_ship'] if firstlastship is not None else None

    #extract profiles
    profile_seasonality = extract_profile(df = df_seasonality, name = row['season'])

    part = product_dict[row['part']]
    listing = Listing(
        part=part,
        prov=row['prov'],
        actuals_type=row['actualstype'],
        loadin=row['loadin'],
        loadzeros=row['loadzeros'],

        #launch overrides
        lor1 = row['lor1'],
        lor2 = row['lor2'],
        lor3 = row['lor3'],
        lor4 = row['lor4'],
        lor5 = row['lor5'],
        lor6 = row['lor6'],

        input_baseline=row['mbase'],
        input_start=row['launchdate'],
        input_exit=row['exitdate'],

        #profiles
        lifecycle_name = row['lifecycle'],
        lifecycle = None,
        lifecycle_start=row['lifecyclestart'],

        promo_name=row['promo'],
        promo = None,
        promo_start=row['promostart'],
        
        season_name=row['season'],
        season = profile_seasonality,
        season_start=row['seasonstart'],

        launchpush=row['launchpush'],
        first_ship = first_ship,
        last_ship = last_ship,
        
        #dicts with dataframes containing part, prov, sow, demand
        depletions = depletions,
        shipments = shipments,

    )
    #add listing to dictionary with SKU and province as key
    listing_key = (row['part'], row['prov'])
    listing_dict[listing_key] = listing

    #print(f"{listing.part.name}{listing.prov}, first ship = {listing.first_ship}, last ship = {listing.last_ship}, status = {listing.long_status}")


print(len(listing_dict), "listings loaded.")


print("complete")


