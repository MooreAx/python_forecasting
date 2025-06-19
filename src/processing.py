import pandas as pd

def fill_and_trim(df):
    """
    Fills missing weeks with 0s and trims leading zeros per (part, prov) group.
    
    Parameters:
    - df: DataFrame with columns ['part', 'prov', 'sow', 'demand']
    
    Returns:
    - A DataFrame with gaps filled and leading zeros trimmed.
    """
    df = df.copy()
    
    # Step 1: Get all part-prov pairs
    part_prov_pairs = df[['part', 'prov']].drop_duplicates()
    
    # Step 2: Generate all weeks across full range
    all_weeks = pd.date_range(df['sow'].min(), df['sow'].max(), freq='W-MON')
    part_prov_pairs['key'] = 1
    weeks_df = pd.DataFrame({'sow': all_weeks, 'key': 1})
    full_index = part_prov_pairs.merge(weeks_df, on='key').drop(columns='key')
    
    # Step 3: Merge to fill missing weeks with 0
    df_filled = (
        full_index
        .merge(df, on=['part', 'prov', 'sow'], how='left')
        .fillna({'demand': 0})
        .sort_values(['part', 'prov', 'sow'])
        .reset_index(drop=True)
    )
    
    # Step 4: Trim leading zeros
    df_filled_trimmed = (
        df_filled
        .assign(cumsum=lambda x: x.groupby(['part', 'prov'])['demand'].cumsum())
        .query("cumsum > 0")
        .drop(columns="cumsum")
        .reset_index(drop=True)
    )

    return df_filled_trimmed