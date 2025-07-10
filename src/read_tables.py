#reads shipments, pos, depletions, inventory, board inventory

import pandas as pd
import janitor as jn
from processing import fill_and_trim
from globals import *

#read files & clean names
df_shipments = pd.read_csv(mape_bias_folder + r"\Intermediates\HDA_raw.csv", dtype = str).clean_names()
df_depletions = pd.read_csv(source_data + r"\Dep Export (New).csv", encoding="utf-16", delimiter="\t", dtype = str).clean_names()
df_board_inventory = pd.read_csv(source_data + r"\Inv Export (New).csv", encoding = "utf-16", delimiter="\t", dtype = str).clean_names()

#clean up

df_shipments = (
    df_shipments
    .rename(columns={"prov2": "prov"})
    .assign(
        sow = lambda x: pd.to_datetime(x['sow']),
        units=lambda x: pd.to_numeric(x['units'], errors='coerce').fillna(0).astype(int)
    )
)

#kind of cumbersome to pass external variables into query. use boolean indexing:
df_shipments = df_shipments[
    (df_shipments["channel"] == "REC") &
    (df_shipments["sow"] <= LASTACTUALS)
]

df_shipments = (
    df_shipments
    .drop(columns=['g_revenue', 'avg_g_price', 'channel'])
    .groupby(['sow', 'part', 'prov'])
    .agg(demand=('units', 'sum'))
    .reset_index()
)
  
df_first_last_ship = (
    df_shipments
    .groupby(['part', 'prov'])
    .agg(
        first_ship=('sow', 'min'),
        last_ship=('sow', 'max')
    )
    .reset_index()
    .assign(partprov = lambda d: d['part'] + d['prov'])
)

df_depletions = (
    df_depletions
    .clean_names()
    .query("licensed_producer == 'CANOPY GROWTH CORP'")
    .rename(columns={
        "week_end_date": "week_end_date_sunday",
        "part_number": "part",
        "unit_volume": "demand",
        "province": "prov"
    })
    .assign(
        week_end_date_sunday = lambda x: pd.to_datetime(x['week_end_date_sunday']),
        sow = lambda x: x['week_end_date_sunday'] - pd.DateOffset(days=6),
        demand=lambda x: pd.to_numeric(x['demand'], errors='coerce').fillna(0).astype(int)
    )
    #select columns
    [['part', 'prov', 'sow', 'demand']]
)

df_board_inventory = (
    df_board_inventory
    .clean_names()
    .query("licensed_producer == 'CANOPY GROWTH CORP'")
    .rename(columns={
        "week_end_date": "week_end_date_sunday",
        "part_number": "part",
        "inventory_qty": "on_hand",
        "on_order_qty": "on_order",
        "ttl_pipeline": "total_inv",
        "province": "prov"
        })
    .assign(
        week_end_date_sunday = lambda x: pd.to_datetime(x['week_end_date_sunday']),
        sow = lambda x: x['week_end_date_sunday'] - pd.DateOffset(days=6),
        on_hand=lambda x: pd.to_numeric(x['on_hand'], errors='coerce').fillna(0).astype(int),
        on_order=lambda x: pd.to_numeric(x['on_order'], errors='coerce').fillna(0).astype(int),
        total_inv=lambda x: pd.to_numeric(x['total_inv'], errors='coerce').fillna(0).astype(int)
    )
    #select columns
    [['part', 'prov', 'sow', 'on_hand', 'on_order', 'total_inv']]
)

#fill missing values with zeros and trim leading zeros
df_shipments = fill_and_trim(df_shipments)
df_depletions = fill_and_trim(df_depletions)

'''
# Display the first few rows
pd.set_option('display.max_rows', None)
print(df_shipments.head())
print(df_depletions.head())
print(df_board_inventory.head())
print(df_first_last_ship.head())
'''

# Save cleaned dataframes to CSV files
df_first_last_ship.to_csv(output_data + r"\first_last_ship.csv", index=False)
df_shipments.to_csv(output_data + r"\shipments.csv", index=False)
df_depletions.to_csv(output_data + r"\depletions.csv", index=False)