import pandas as pd
import numpy as np
import requests
from sqlalchemy import create_engine

def pretvori_zupaniju_u_regiju(df, zupanija_u_regiju):
    df = df.drop('County of', axis=1)
    df['regija'] = df['Županija'].map(zupanija_u_regiju)
    df_grouped = df.groupby('regija').sum().reset_index()
    df_grouped = df_grouped.drop(columns="Županija", errors='ignore')
    df_grouped.columns = [col.split('.')[0] for col in df_grouped.columns]
    return df_grouped

def fetch_zaposlenost_data():
    url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tgs00007?geo=HR02&geo=HR03&geo=HR05&geo=HR06&time=2012&time=2013&time=2014&time=2015&time=2016&time=2017&time=2018&time=2019&time=2020&time=2021&time=2022&time=2023&format=JSON"
    response = requests.get(url)
    data = response.json()
    
    geo_map = data["dimension"]["geo"]["category"]["label"]
    time_map = data["dimension"]["time"]["category"]["label"]
    values = data["value"]
    
    rows = []
    geo_keys = list(geo_map.keys())
    time_keys = list(time_map.keys())
    for key, value in values.items():
        region_index, time_index = divmod(int(key), len(time_keys))
        if region_index >= len(geo_keys) or time_index >= len(time_keys):
            continue
        region_code = geo_keys[region_index]
        year = time_keys[time_index]
        rows.append({
            "Region": geo_map[region_code],
            "Year": year,
            "Employment Rate": value
        })
    
    return pd.DataFrame(rows)

def melt_and_merge_data(df_ucenici, df_zaposlenost, df_studenti, df_diplomirani):
    df_ucenici_melted = pd.melt(df_ucenici, id_vars=['regija'], var_name='Godina', value_name='Broj Ucenika')
    df_zaposlenost_melted = pd.melt(df_zaposlenost, id_vars=['Region'], var_name='Godina', value_name='Postotak Zaposlenosti')
    df_zaposlenost_melted = df_zaposlenost_melted.rename(columns={'Region': 'regija'})
    df_zaposlenost_melted = df_zaposlenost_melted.drop_duplicates(subset=['regija', 'Godina'])

    combined_se = pd.merge(df_ucenici_melted, df_zaposlenost_melted, on=['regija', 'Godina'], how='inner')

    df_studenti_melted = pd.melt(df_studenti, id_vars=['regija'], var_name='Godina', value_name='Broj Studenata')
    df_studenti_melted = df_studenti_melted.drop_duplicates(subset=['regija', 'Godina'])
    combined_sef = pd.merge(combined_se, df_studenti_melted, on=['regija', 'Godina'], how='inner')

    df_diplomirani_melted = pd.melt(df_diplomirani, id_vars=['regija'], var_name='Godina', value_name='Broj Diplomiranih Studenata')
    df_diplomirani_melted = df_diplomirani_melted.drop_duplicates(subset=['regija', 'Godina'])
    combined_final = pd.merge(combined_sef, df_diplomirani_melted, on=['regija', 'Godina'], how='inner')

    return combined_final.drop_duplicates()

#  ------------------------------------------------------------------------- #
#  ------------------------------ glavni dio  ------------------------------ #
#  ------------------------------------------------------------------------- #

# Excel data
df_obrazovanje_srednje = pd.read_excel("obrazovanje.xlsx", sheet_name="8.1.3. ")
df_obrazovanje_fakultet = pd.read_excel("obrazovanje.xlsx", sheet_name="8.1.4.")
df_obrazovanje_fakultet_diplomirani = pd.read_excel("obrazovanje.xlsx", sheet_name="8.1.5.")

zupanija_regija = {
    "Zagrebačka": "Sjeverna Hrvatska",
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
    "Grad Zagreb": "Grad Zagreb"
}

processed_srednje = pretvori_zupaniju_u_regiju(df_obrazovanje_srednje, zupanija_regija)
processed_fakultet = pretvori_zupaniju_u_regiju(df_obrazovanje_fakultet, zupanija_regija)
processed_fakultet_diplomirani = pretvori_zupaniju_u_regiju(df_obrazovanje_fakultet_diplomirani, zupanija_regija)

# Json data
df_json = fetch_zaposlenost_data()
pivot_df = df_json.pivot(index="Region", columns="Year", values="Employment Rate").reset_index()

# Prebacivanje iz multindeks tu jednostavni indeks
pivot_df.columns = ['Region'] + [str(col) for col in pivot_df.columns[1:]]

# Spajanje svih podataka
df_combined = melt_and_merge_data(processed_srednje, pivot_df, processed_fakultet, processed_fakultet_diplomirani)

# slanje na  PostgreSQL
engine = create_engine('postgresql://postgres:root@localhost:5432/data')
df_combined.to_sql('datanal', engine, if_exists='replace', index=False)

print("Podaci uspjesno poslani u PostgreSQL !")