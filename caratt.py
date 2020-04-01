import pandas as pd

s = set()

df = pd.read_csv("./scraper/immobiliare_ads_2020-03-03.csv")

df = df.dropna(subset=["CARATTERISTICHE"])

for i, it in df['CARATTERISTICHE'].iteritems():
    li = it.lower().split(";")
    for j in li:
        s.add(j)

# print(s)

# {'camino', 'porta blindata', 'cantina', 'infissi esterni in triplo vetro / pvc',
#  'infissi esterni in triplo vetro / legno', 'infissi esterni in doppio vetro / metallo', 'parzialmente arredato',
#  'impianto tv con parabola satellitare', 'impianto tv centralizzato', 'infissi esterni in doppio vetro / pvc',
#  'esposizione esterna', 'balcone', 'infissi esterni in doppio vetro / legno', 'terrazza', 'piscina', 'idromassaggio',
#  'portiere mezza giornata', 'impianto tv singolo', 'impianto allarme', 'esposizione interna', 'mansarda',
#  'esposizione doppia', 'infissi esterni in triplo vetro / metallo', 'giardino privato', 'giardino comune',
#  'infissi esterni in vetro / pvc', 'portiere intera giornata', 'infissi esterni in vetro / legno', 'cancello elettrico',
#  'fibra ottica', 'armadio a muro', 'infissi esterni in vetro / metallo', 'solo cucina arredata', 'taverna',
#  'campo da tennis', 'arredato', 'videocitofono', 'non arredato'}

char_dict = {'camino': 0, 'porta blindata': 0, 'cantina': 0, 'infissi esterni in triplo vetro / metallo': 0,
             'numero_vetri': 0, 'materiale_infisso': 0, 'arredo': 0, 'portiere': 0, 'impianto tv': 0, 'giardino': 0,
             'esposizione': 0, 'balcone': 0, 'terrazza': 0, 'piscina': 0, 'idromassaggio': 0, 'impianto allarme': 0,
             'mansarda': 0, 'cancello elettrico': 0, 'fibra ottica': 0,  'taverna': 0, 'campo da tennis': 0,
             'videocitofono': 0}