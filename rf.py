import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor


def main():

    # remove buildingYear for the time being because of the missing values

    df = pd.read_csv('data/immobiliare_ads_Cambiasca_Vignone_Bee_Arizzano_Premeno_2023-08-12_16:28:31.csv')

    df = df.dropna(subset=['price', 'latitude', 'longitude'])

    df['airConditioning'] = df['airConditioning'].apply(lambda x: 0 if pd.isna(x) else 1)

    # booleans
    df['hasElevators'] = (df['hasElevators']==True).astype(int)

    # regex
    df['surface'] = df['surface'].str.extract(r"(\d+)")
    df['floors'] = df['floors'].str.extract(r"(\d+)")

    df['rooms'] = df['rooms'].str.extract(r"(\d+)")  # don't handle thinks like 5+
    df['bathrooms'] = df['bathrooms'].str.extract(r"(\d+)")  # same

    df['condoExpenses'] = df['condoExpenses'].str.extract(r"(\d+)")
    df['condoExpenses'].fillna(0, inplace=True)

    # binary
    binary_columns = ['Porta blindata', 'balcone', 'terrazza', 'impianto tv singolo', 'Parzialmente Arredato',
                      'Giardino comune', 'Infissi esterni in doppio vetro / PVC', 'Esposizione esterna',
                      'impianto tv con parabola satellitare', 'cantina', 'Giardino privato e comune',
                      'Infissi esterni in vetro / legno', 'cancello elettrico', 'Caminetto','Mansarda', 'Taverna',
                      'videoCitofono', 'Impianto di allarme', 'Giardino privato', 'Esposizione doppia', 'Armadio a muro',
                      'Infissi esterni in doppio vetro / legno', 'Solo Cucina Arredata', 'Infissi esterni in doppio vetro / metallo',
                      'impianto tv centralizzato', 'Idromassaggio', 'piscina', '2 balconi', 'Arredato', 'Fibra ottica',
                      'Infissi esterni in vetro / metallo', 'Esposizione interna', 'Cucina','Infissi esterni in triplo vetro / PVC',
                      'esposizione est', '1 balcone', 'Infissi esterni in triplo vetro / legno', 'Campo da tennis',
                      'Reception', 'portiere mezza giornata']
    df.loc[:, binary_columns] = df.loc[:, binary_columns].fillna(0)

    # missing values
    df['bathrooms'].fillna(1, inplace=True)  # assume at least 1
    df['bedRoomsNumber'].fillna(1, inplace=True)  # assume at least 1

    ct = ColumnTransformer(
        [
            ('one-hot', OneHotEncoder(), ['typology', 'condition', 'category', 'heatingType', 'airConditioning']),
            ('pass', 'passthrough', ['rooms', 'bathrooms', 'bedRoomsNumber', 'latitude', 'longitude'] + binary_columns)
        ]
    )

    rf = RandomForestRegressor(verbose=2, random_state=2023)

    feat = ct.fit_transform(df)

    rf.fit(feat, df['price'])

    sample = {
        'id': np.nan,
        'createdAt': np.nan,
        'updatedAt': np.nan,
        'contract': np.nan,
        'price': 0,
        'typology': 'Casa indipendente',
        'availability': np.nan,
        'condition': 'Buono / Abitabile',  # 'Da ristrutturare',
        'buildingYear': 1980,
        'rooms': 3,
        'bathrooms': 2,
        'bedRoomsNumber': 2,
        'hasElevators': 0,
        'surface': 120,
        'floors': 1,
        'garage': '1 in box privato/box in garage',
        'floor': np.nan,
        'category': 'Residenziale',
        'condoExpenses': 0,
        'expenses': np.nan,
        'heatingType': 'autonomo, a radiatori, alimentato a metano',
        'airConditioning': 0,
        'class': 'G',
        'latitude': 45.95080882795933,
        'longitude': 8.586238256308775,
        'Porta blindata': 0,
        'balcone': 1,
        'terrazza': 1,
        'impianto tv singolo': 0,
        'Parzialmente Arredato': 0,
        'Giardino comune': 0,
        'Infissi esterni in doppio vetro / PVC': 0,
        'Esposizione esterna': 1,
        'impianto tv con parabola satellitare': 0,
        'cantina': 1,
        'Giardino privato e comune': 0,
        'Infissi esterni in vetro / legno': 0,
        'cancello elettrico': 0,
        'Caminetto': 1,
        'Mansarda': 0,
        'Taverna': 0,
        'videoCitofono': 0,
        'Impianto di allarme': 0,
        'Giardino privato': 0,
        'Esposizione doppia': 1,
        'Armadio a muro': 0,
        'Infissi esterni in doppio vetro / legno': 0,
        'Solo Cucina Arredata': 0,
        'Infissi esterni in doppio vetro / metallo': 0,
        'impianto tv centralizzato': 0,
        'Idromassaggio': 0,
        'piscina': 0,
        '2 balconi': 0,
        'Arredato': 0,
        'Fibra ottica': 0,
        'Infissi esterni in vetro / metallo': 0,
        'Esposizione interna': 1,
        'Cucina': 1,
        'Infissi esterni in triplo vetro / PVC': 0,
        'esposizione est': 0,
        '1 balcone': 1,
        'Infissi esterni in triplo vetro / legno': 0,
        'Campo da tennis': 0,
        'Reception': 0,
        'portiere mezza giornata': 0
    }

    # sample_feat = ct.transform(pd.read_csv('data/sample_ads.csv'))
    sample_feat = ct.transform(pd.DataFrame([sample]))
    print(rf.predict(sample_feat))


if __name__ == "__main__":
    main()
