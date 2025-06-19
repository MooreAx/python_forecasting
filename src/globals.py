#global variables

from datetime import datetime, timedelta

PUBLISH_DATE = datetime(2025, 6, 20)
FCSTART = PUBLISH_DATE + timedelta(days=3)
CURRENTWK = PUBLISH_DATE - timedelta(days=4)

#dates
MINDATE = datetime(2000,1,1)
MAXDATE = datetime(2030,1,1)


#paths
mape_bias_folder = r"C:\Users\alex.moore\OneDrive - Canopy Growth Corporation\Documents\Working Folder\R\mape_bias"
source_data = r"C:\Users\alex.moore\OneDrive - Canopy Growth Corporation\Documents\Working Folder\python_forecasting\source-data"
output_data = r"C:\Users\alex.moore\OneDrive - Canopy Growth Corporation\Documents\Working Folder\python_forecasting\output-data"
