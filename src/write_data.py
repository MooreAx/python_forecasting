#write listing data to csv

from forecast import listing_dict
import pandas as pd
from globals import *

rows = []
fcdata = []

for (part, prov), listing in listing_dict.items():
    #general data
    rows.append({
        'part': listing.part.name,
        'prov': listing.prov,
        'short_status': listing.short_status,
        'long_status': listing.long_status,
        'n_depletions': listing.n_depletions,
        'n_shipments': listing.n_shipments,
        'depletions_baseline': listing.depletions_baseline,
        'shipments_baseline': listing.shipments_baseline,
        'calc_baseline': listing.calc_baseline,
        'log': listing.log,
    })

    #forecast data
    if len(listing.fc) > 0:
        for week, qty, type in listing.fc:
            fcdata.append({
                'part': listing.part.name,
                'prov': listing.prov,
                'week': week,
                'qty': qty,
            })


# Convert to DataFrame
df = (pd.DataFrame(rows)
      .assign(
          partprov = lambda d: d['part'] + d['prov'],
      )
)

df_fc = pd.DataFrame(fcdata)

print(df_fc.head(20))

cutoff_date = datetime(2027, 4, 1)


df_fc_pivot = (
    df_fc
    .query("week < @cutoff_date")
    .query("week >= @FCSTART")
    .assign(
        partprov=lambda d: d['part'] + d['prov'],
        week=lambda d: pd.to_datetime(d['week']).dt.date # Drop time
    )
    .pivot(index='partprov', columns='week', values='qty')
    .fillna(0)
    .astype(int)
    .reset_index()
)

# Export to CSV
df.to_csv(output_data + r'\listing_status.csv', index=False)
df_fc_pivot.to_csv(output_data + r'\forecast.csv', index=False)
