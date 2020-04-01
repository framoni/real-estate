import numpy as np
import pandas as pd
import re

"""
Clean the data of ads taken from immobiliare.it
"""

# IMPORTANT: evaluate the possibility to retrieve missing infos (or predict them)

# load the dataset
df = pd.read_csv("./scraper/immobiliare_ads_2020-03-03.csv")

# CONTRATTO
# ignore column "Contratto" as we know that all the scraped ads are about houses for sale
df = df.drop(columns=['CONTRATTO'])

# ASTE GIUDIZIARIE
# exclude judicial auctions
# remove PROCEDURA when different from nan
# remove descriptions and titles with occurrances of "asta giudiziaria", "all'asta"
df = df.loc[pd.isna(df["PROCEDURA"])]
df_ja = df.loc[df['DESCRIZIONE'].str.contains("all'asta") | df['DESCRIZIONE'].str.contains("asta giudiziaria") |
               df['TITOLO'].str.contains("all'asta") | df['TITOLO'].str.contains("asta giudiziaria")]
df = df.drop(index=df_ja.index)

# TIPO PROPRIETA'
df = df.dropna(subset=["TIPO PROPRIETÀ"])
tp_list = []
for it, tp_str in df['TIPO PROPRIETÀ'].iteritems():
    if any(word in tp_str.lower() for word in ["nuda", "multi", "superficie", "parziale"]):
        tp_list.append("to_drop")
    else:
        if "economica" in tp_str:
            tp_list.append(0)
        elif "media" in tp_str:
            tp_list.append(1)
        elif "lusso" in tp_str or "signorile" in tp_str:
            tp_list.append(2)
        else:
            tp_list.append("to_drop")  # ?
df['TIPO PROPRIETÀ'] = tp_list
df = df[df["TIPO PROPRIETÀ"] != "to_drop"]

# SUPERFICIE
# search the (first) occurrance of "_ m2" or "_ m²" in the "Superficie" column, if any
sup_list = []
for it, sup in df['SUPERFICIE'].iteritems():
    if pd.isna(sup):
        sup_list.append(sup)
        continue
    sup = sup.replace("\n", "")
    matches = re.findall('\d+\s*m²*2*', sup)
    if len(matches) > 0:
        # here we discard occurrances other than the first one in each field; this way we exclude
        # "area for commercial purposes" (acceptable) but also the eventual area of a garden and/or courtyard
        digits = re.findall('\d+', matches[0])
        sup_list.append(digits[0])
df['SUPERFICIE'] = sup_list

# TIPOLOGIA
# this was used to export the house types to Google Sheets
# tipologie = df['TIPOLOGIA'].unique().tolist()
# tipologie = [t.replace("\n", " ") for t in tipologie]

# drop house types that are nan
df = df.dropna(subset=["TIPOLOGIA"])
# remove line breaks
df['TIPOLOGIA'] = df['TIPOLOGIA'].apply(lambda x: x.replace("\n", " "))
# build type mappings
type_map_df = pd.read_csv("./type_mapping.csv")
type_map = pd.Series(type_map_df['To'].values, index=type_map_df['From']).to_dict()
# map typologies
df['TIPOLOGIA'] = df['TIPOLOGIA'].map(type_map)

# LOCALI
df = df.dropna(subset=["LOCALI"])
room_list = []
for it, loc in df['LOCALI'].iteritems():
    loc = loc.replace("+", " ")
    room_dict = {'CUCINE': 0, 'BAGNI': 0, 'CAMERE_LETTO': 0, 'ALTRO': 0}
    matches = re.findall('\d*\s*[a-z]+[a-z\s]*', loc)
    for match in matches:
        if "bagn" in match:
            room_dict['BAGNI'] = int(re.findall('\d+', match)[0])
        elif "lett" in match:
            room_dict['CAMERE_LETTO'] = int(re.findall('\d+', match)[0])
        elif "cucin" in match:
            try:
                room_dict['CUCINE'] = int(re.findall('\d+', match)[0])
            except IndexError:
                room_dict['CUCINE'] = 1
        else:
            room_dict['ALTRO'] = int(re.findall('\d+', match)[0])
    room_dict['TOT_STANZE'] = np.sum(list(room_dict.values()))
    room_list.append(room_dict)
room_df = pd.DataFrame(data=room_list)
df = df.drop(columns=["LOCALI"])
df = df.reset_index(drop=True)
df = pd.concat([df, room_df], axis=1)

# BOX E POSTO AUTO
bpa_list = []
for it, bpa in df['BOX E POSTO AUTO'].iteritems():
    bpa_dict = {'BOX': 0, 'POSTO AUTO': 0}
    if pd.isna(bpa):
        bpa_list.append(bpa_dict)
        continue
    bpa = bpa.lower().split(",")
    for item in bpa:
        if "box" in item:
            try:
                bpa_dict['BOX'] = int(re.findall('\d+', item)[0])
            except IndexError:
                bpa_dict['BOX'] = 1
        elif "post" in item:
            bpa_dict['POSTO AUTO'] = int(re.findall('\d+', item)[0])
    bpa_list.append(bpa_dict)
bpa_df = pd.DataFrame(data=bpa_list)
df = df.drop(columns=["BOX E POSTO AUTO"])
df = df.reset_index(drop=True)
df = pd.concat([df, bpa_df], axis=1)

# DISPONIBILITA'
df['DISPONIBILITÀ'] = df['DISPONIBILITÀ'].fillna("Non libero")

# PIANO
# find missing info in descriptions or notes?
df = df.dropna(subset=["PIANO"])
floor_list = []
for it, floor_str in df['PIANO'].iteritems():
    floor_dict = {'PIANO': 0, 'DELTA_PIANO': 0, 'ASCENSORE': 0}
    floor_str = floor_str.lower().split(",")
    for s in floor_str:
        if "ascensore" in s:
            floor_dict['ASCENSORE'] = 1
    matches = re.findall('\d', floor_str[0])
    if len(matches) == 2:
        floor_dict['PIANO'] = int(matches[0])
        floor_dict['DELTA_PIANO'] = int(matches[1]) - int(matches[0])
    elif len(matches) == 1:
        # floor = floor_str[0].split("di")
        # if any(["ultimo" in s for s in floor]):
        floor = floor_str[0]
        if "ultimo" in floor:
            floor_dict['PIANO'] = int(matches[0])
            floor_dict['DELTA_PIANO'] = 0
        elif "piano terra" in floor or "rialzato" in floor or "ammezzato" in floor:
            floor_dict['PIANO'] = 0
            floor_dict['DELTA_PIANO'] = int(matches[0])
        elif "seminterrato" in floor:
            floor_dict['PIANO'] = -1
            floor_dict['DELTA_PIANO'] = int(matches[0]) + 1  # to rethink
        else:
            floor_dict['PIANO'] = int(matches[0])
            floor_dict['DELTA_PIANO'] = -5  # DELTA_PIANO needs to be discarded if this is not solved with more scraping
            # print("Something else as floor: ", floor_str)
    floor_list.append(floor_dict)
floor_df = pd.DataFrame(data=floor_list)
df = df.drop(columns=["PIANO"])
df = df.reset_index(drop=True)
df = pd.concat([df, floor_df], axis=1)

# PREZZO
df = df.dropna(subset=["PREZZO"])
price_list = []
on_request = []
for it, price in df['PREZZO'].iteritems():
    price = price.lower().replace(".", "")
    match = re.findall('vendita\s*€\s*(\d+)', price)
    if len(match) == 0:
        on_request.append(it)
    else:
        price_list.append(int(match[0]))
df = df.drop(labels=on_request)
df['PREZZO'] = price_list

# SPESE CONDOMINIO

# ANNO DI COSTRUZIONE
# find missing info in descriptions or notes?
df = df.dropna(subset=["ANNO DI COSTRUZIONE"])
# df["ANNO DI COSTRUZIONE"] = df["ANNO DI COSTRUZIONE"].astype("int")

# STATO
# 3: Nuovo
# 2: Ristrutturato
# 1: Abitabile
# 0: Da ristrutturare

df = df.dropna(subset=["STATO"])
try:
    df = df.drop(df.loc[df["STATO"] == "Partecipabile"])
    df = df.drop(df.loc[df["STATO"] == "Non partecipabile"])
except KeyError:
    pass
# quality_map = {'Nuovo / In costruzione': 'Nuovo', 'Ottimo / Ristrutturato': 'Ristrutturato',
#                'Buono / Abitabile': 'Abitabile', 'Da ristrutturare': 'Da ristrutturare'}
quality_map = {'Nuovo / In costruzione': 3, 'Ottimo / Ristrutturato': 2,
               'Buono / Abitabile': 1, 'Da ristrutturare': 0}
df['STATO'] = df['STATO'].map(quality_map)

# INDICE DI PRESTAZIONE ENERGETICA GLOBALE (EP_GL,NREN)
# don't consider this variable for now

# RISCALDAMENTO
# 0: centralizzato
# 1: autonomo
# 2: assente
# if nan => absent
df['RISCALDAMENTO'] = df['RISCALDAMENTO'].fillna(value="assente")
other = []
df = df.reset_index(drop=True)
for it, heating in df['RISCALDAMENTO'].iteritems():
    heating = heating.lower()
    if "centralizzato" in heating:
        df['RISCALDAMENTO'].iloc[it] = "centralizzato"
    elif "autonomo" in heating:
        df['RISCALDAMENTO'].iloc[it] = "autonomo"
    elif "assente" in heating:
        df['RISCALDAMENTO'].iloc[it] = "assente"
    else:
        other.append(it)
        # print("Something else as heating: ", heating)
df = df.drop(labels=other)

# CONDIZIONATORE
# 0: no air conditioning
# 1: air conditioning
df = df.reset_index(drop=True)
df['CONDIZIONATORE'] = df['CONDIZIONATORE'].fillna(value="assente")
for it, cond in df['CONDIZIONATORE'].iteritems():
    cond = cond.lower()
    if "assente" in cond or "predispos" in cond:
        df['CONDIZIONATORE'].iloc[it] = 0
    else:
        df['CONDIZIONATORE'].iloc[it] = 1
# exclude hot-air-only as it's rare (about 20 occurrances)
df['CONDIZIONATORE'].loc[df['CONDIZIONATORE'].isin(['Assente, solo caldo', 'Predisposizione impianto, solo caldo',
                                                    'Centralizzato, solo caldo', 'Autonomo, solo caldo'])] = 0

# CLASSE ENERGETICA
df['CLASSE ENERGETICA'] = df['CLASSE ENERGETICA'].fillna(value="NC")
ce_list = []
for it, ce in df['CLASSE ENERGETICA'].iteritems():
    ce = ce.split(",")[0]
    if "A" in ce:
        ce = "A"
    elif ce in ["B", "C", "D", "E", "F", "G"]:
        pass
    else:
        ce = "NC"
    ce_list.append(ce)
df['CLASSE ENERGETICA'] = ce_list
df = df[df["CLASSE ENERGETICA"] != "NC"]
ce_map = {'A': 6, 'B': 5, 'C': 4, 'D': 3, 'E': 2, 'F': 1, 'G': 0}
df['CLASSE ENERGETICA'] = df['CLASSE ENERGETICA'].map(ce_map)

# COORDINATE GEOGRAFICHE
df = df.dropna(subset=["LAT", "LONG"])
c = [45.46425, 9.1887274]  # map center (Duomo di Milano)
coord_list = []
for it, coord in df[['LAT', 'LONG']].iterrows():
    p = (coord['LAT'], coord['LONG'])
    p = [(x - y) * 1000 for x, y in zip(p, c)]
    coord_list.append(p)
df[['LAT', 'LONG']] = coord_list

# CARATTERISTICHE
char_list = []
for i, it in df['CARATTERISTICHE'].iteritems():
    char_dict = {'camino': 0, 'porta blindata': 0, 'cantina': 0, 'numero vetri': 0, 'mat legno': 0, 'mat pvc': 0,
                 'mat al': 0, 'arredo': 0, 'portiere': 0, 'impianto tv': 0, 'giardino': 0,
                 'esposizione interna': 0, 'esposizione esterna': 0, 'esposizione doppia': 0, 'balcone': 0,
                 'terrazza': 0, 'piscina': 0, 'idromassaggio': 0, 'impianto allarme': 0,
                 'mansarda': 0, 'cancello elettrico': 0, 'fibra ottica': 0, 'taverna': 0, 'campo da tennis': 0,
                 'videocitofono': 0}
    if pd.isna(it):
        char_list.append(char_dict)
        continue
    li = it.lower().split(";")
    for j in li:
        if j in char_dict.keys():
            char_dict[j] = 1
    if "vetro" in it.lower():
        if "doppio vetro" in it.lower():
            char_dict['numero vetri'] = 2
        elif "triplo vetro" in it.lower():
            char_dict['numero vetri'] = 3
        else:
            char_dict['numero vetri'] = 1
        if "legno" in it.lower():
            char_dict['mat legno'] = 1
        elif "pvc" in it.lower():
            char_dict['mat pvc'] = 1
        elif "metallo" in it.lower():
            char_dict['mat al'] = 1
    if "non arredato" in it.lower():
        char_dict['arredo'] = 0
    elif "parzialmente arredato" in it.lower():
        char_dict['arredo'] = 1
    elif "arredato" in it.lower():
        char_dict['arredo'] = 2
    if "portiere" in it.lower():
        char_dict['portiere'] = 1
    if "giardino comune" in it.lower():
        char_dict['giardino'] = 1
    elif "giardino privato" in it.lower():
        char_dict['giardino'] = 2
    if "impianto tv" in it.lower():
        char_dict['impianto tv'] = 1
    char_list.append(char_dict)
char_df = pd.DataFrame(data=char_list)
df = df.drop(columns=["CARATTERISTICHE"])
df = df.reset_index(drop=True)
df = pd.concat([df, char_df], axis=1)

# analyze ad description (to be done better with NLP)
df = df[-df["DESCRIZIONE"].str.contains("nuda propriet", na=False)]

df = df[['DATA-ID', 'TITOLO', 'LAT', 'LONG', 'TIPOLOGIA', 'TIPO PROPRIETÀ', 'SUPERFICIE', 'PREZZO',
         'ANNO DI COSTRUZIONE', 'STATO', 'RISCALDAMENTO', 'CONDIZIONATORE', 'CLASSE ENERGETICA', 'DISPONIBILITÀ',
         'CUCINE', 'BAGNI', 'CAMERE_LETTO', 'ALTRO', 'TOT_STANZE', 'BOX', 'POSTO AUTO', 'PIANO', 'DELTA_PIANO',
         'ASCENSORE'] + list(char_dict.keys())]

# FIND AND DROP DUPLICATES
# prone to error when e.g. no civic number
# sub = ['INDIRIZZO', 'PIANO', 'SUPERFICIE']

df.to_csv("./immobiliare_ads_clean_2020-03-03.csv", index=False)
