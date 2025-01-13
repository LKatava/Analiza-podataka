import pandas as pd
import numpy as np
import requests

#Excel
df_obrazovanje_srednje = pd.read_excel("obrazovanje.xlsx",sheet_name="8.1.3. ")
df_obrazovanje_fakultet = pd.read_excel("obrazovanje.xlsx",sheet_name="8.1.4.")
df_obrazovanje_diplomirani = pd.read_excel("obrazovanje.xlsx",sheet_name="8.1.5.")

df_obrazovanje_srednje=df_obrazovanje_srednje.drop('County of',axis=1)
df_obrazovanje_fakultet=df_obrazovanje_fakultet.drop('County of',axis=1)
df_obrazovanje_diplomirani=df_obrazovanje_diplomirani.drop('County of',axis=1)

#Json
url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tgs00007?geo=HR02&geo=HR03&geo=HR05&geo=HR06&time=2012&time=2013&time=2014&time=2015&time=2016&time=2017&time=2018&time=2019&time=2020&time=2021&time=2022&time=2023&format=JSON"
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

zupanija_u_regiju = {
    "Zagrebačka" : "Sjeverna Hrvatska",
    "Krapinsko-zagorska": "Sjeverna Hrvatska",
    "Sisačko-moslavačka": "Panonska Hrvatska",
    "Karlovačka": "Panonska Hrvatska",
    "Varaždinska": "Sjeverna Hrvatska",
    "Koprivničko-križevačka": "Sjeverna Hrvatska",
    "Bjelovarsko-bilogorska": "Panonska Hrvatska",
    "Primorsko-goranska": "Jadranska Hrvatska",
    "Ličko-senjska": "Jadranska Hrvatska",
    "Virovitičko-podravska": "Panonska Hrvatska",
    "Požeško-slavonska": "Panonska Hrvatska",
    "Brodsko-posavska": "Panonska Hrvatska",
    "Zadarska": "Jadranska Hrvatska",
    "Osječko-baranjska": "Panonska Hrvatska",
    "Šibensko-kninska": "Jadranska Hrvatska",
    "Vukovarsko-srijemska": "Panonska Hrvatska",
    "Splitsko-dalmatinska": "Jadranska Hrvatska",
    "Istarska": "Jadranska Hrvatska",
    "Dubrovačko-neretvanska": "Jadranska Hrvatska",
    "Međimurska": "Sjeverna Hrvatska",
    "Grad Zagreb":"Grad Zagreb"
}

df_obrazovanje_srednje['regija'] = df_obrazovanje_srednje['Županija'].map(zupanija_u_regiju)
df_grupirana_srednja = df_obrazovanje_srednje.groupby('regija').sum().reset_index()

df_grupirana_srednja=df_grupirana_srednja.drop(columns="Županija")

pivot_df = df_json.pivot(index="Region",columns="Year",values="Employment Rate")

df_cut_srednja = df_grupirana_srednja.drop(columns={'2005./2006.', '2006./2007.', '2007./2008.', '2008./2009.',
       '2009./2010.', '2010./2011.','2011./2012.'})

df_cut_srednja.columns = [col.split('.')[0] for col in df_cut_srednja.columns]

df_simple = pivot_df.reset_index()

df_simple.columns = ['Region'] + [str(col) for col in df_simple.columns[1:]]

df_students_melted = pd.melt(
    df_cut_srednja, 
    id_vars=['regija'], 
    var_name='Godina', 
    value_name='Broj Studenata'
)

# Unpivot employment dataframe
df_employment_melted = pd.melt(
    df_simple, 
    id_vars=['Region'], 
    var_name='Godina', 
    value_name='Postotak Zaposlenosti'
)

# Prilagodba naziva stupaca za regiju
df_employment_melted = df_employment_melted.rename(columns={'Region': 'regija'})

df_combined = pd.merge(
    df_students_melted, 
    df_employment_melted, 
    on=['regija', 'Godina']
)

from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:root@localhost:5432/data')
df_combined.to_sql('srednja', engine, if_exists='replace', index=False)

print("Data successfully written to PostgreSQL")