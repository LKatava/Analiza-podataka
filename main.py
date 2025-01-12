import pandas as pd
import numpy as np
import requests

#Excel
df_obrazovanje_srednje = pd.read_excel("obrazovanje.xlsx",sheet_name="8.1.3. ")
df_obrazovanje_fakultet = pd.read_excel("obrazovanje.xlsx",sheet_name="8.1.4. ")
df_obrazovanje_diplomirani = pd.read_excel("obrazovanje.xlsx",sheet_name="8.1.5. ")

df_obrazovanje_srednje=df_obrazovanje_srednje.drop('County of',axis=1)
df_obrazovanje_fakultet=df_obrazovanje_fakultet.drop('County of',axis=1)
df_obrazovanje_diplomirani=df_obrazovanje_diplomirani.drop('County of',axis=1)

#Json
url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tgs00007?geo=HR02&geo=HR03&geo=HR05&geo=HR06&time=2021&time=2022&time=2023&format=JSON"
response = requests.get(url)
data = response.json()

geo_map = data["dimension"]["geo"]["category"]["label"]  # Maps geo index to names
time_map = data["dimension"]["time"]["category"]["label"]  # Maps time index to years
values = data["value"]  # Prosjek zapošljenosti

rows = []
geo_keys = list(geo_map.keys()) # index za lokaciju
time_keys = list(time_map.keys()) # index za godine

for key, value in values.items():
    region_index, time_index = divmod(int(key), len(time_keys))
    
    # provjera u slučaju greške ili prelaženja indeksa
    if region_index >= len(geo_keys) or time_index >= len(time_keys):
        continue

    # index u kod
    region_code = geo_keys[region_index]
    year = time_keys[time_index]

    rows.append({
        "Region": geo_map[region_code],
        "Year": year,
        "Employment Rate": value
    })

df_json = pd.DataFrame(rows)