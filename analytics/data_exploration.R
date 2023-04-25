library(corrr)
library(tidyverse)

df <- read.csv("data/immobiliare_ads_clean_2023-01-07.csv")

# rimuoviamo righe con valori mancanti nelle colonne studiate

df <- df %>% drop_na(superficie, prezzo, anno.di.costruzione, lat, lon)

# consideriamo appartamenti con superficie < 200mq e anno di costruzione > 1800

df <- df %>% filter(superficie <= 200, anno.di.costruzione >= 1800)

rplot(correlate(df)) 

# unica variabile che correla fortemente con il prezzo è la superficie
# altre variabili hanno correlazioni deboli (e.g. anno di costruzione) ma 
# risultano significative quando usate nel modello lineare in quanto
# contribuiscono a spiegare la variabilità del prezzo sebbene in misura molto
# minore rispetto alla superficie

# plottiamo prezzo / superficie colorando categorie di anno di costruzione

df <- df %>% mutate(range_adc=cut(anno.di.costruzione, breaks=c(-Inf, 1920, 1950, 1980, 2000, Inf), labels=c("<1920", "1920-1950","1950-1980","1980-2000",">2000")))

ggplot(data=df) + 
  geom_smooth(mapping=aes(x=superficie, y=prezzo, color=range_adc), se=F)

ggplot(data=df) + 
  geom_smooth(mapping=aes(x=superficie, y=prezzo)) + 
  geom_point(mapping=aes(x=superficie, y=prezzo)) +
  facet_wrap(~range_adc, nrow=3)

# la maggior parte degli immobili è inferiore a 125mq di superficie

# non si osserva un netto trend di crescita di prezzo all'aumentare dell'anno 
# di costruzione (a parità di superficie). Può esserci di mezzo l'effetto di 
# un'altra variabile, come la distanza dal centro?

# creaiamo la variabile ro che indica la distanza dal centro di Milano (il Duomo)

duomo_lat <- 45.46464
duomo_lon <- 9.1945

df <- df %>% mutate(d_lat=abs(duomo_lat-lat), d_lon=abs(duomo_lon-lon), 
              d_lat_km=d_lat*110.574, d_lon_km=d_lon*111.320*cos(lat*pi/180),
              ro=sqrt((lat-duomo_lat)^2+(lon-duomo_lon)^2),
              ro_km=sqrt(d_lat_km^2+d_lon_km^2))

# l'appartamento "Milano, Via Bettino da Trezzo, 14" ha coordinate sbagliate che
# risultano in una distanza outlier, e ci sono altri errori a giudicare dall'istogramma

df <- df %>% filter(ro_km<=10) # mettiamo un cap alla distanza dal centro

ggplot(data=df) + geom_histogram(mapping=aes(x=ro_km), binwidth=1)

# analizziamo la correlazione tra distanza e prezzo, e distanza e anno di costruzione

cor.test(df$prezzo, df$ro_km)

# correlazione significativa e negativa come aspettato 

cor.test(df$ro_km, df$anno.di.costruzione)

# correlazione significativa e positiva come aspettato

df <- df %>% mutate(range_sup=cut(superficie, breaks=c(-Inf, 50, 80, 120, Inf), 
                                  labels=c("mono", "bi","tri","quad")))
ggplot(data=df) + 
  geom_smooth(mapping=aes(x=ro_km, y=prezzo, color=range_sup), se=F)

ggplot(data=df) + 
  geom_smooth(mapping=aes(x=ro_km, y=prezzo)) + 
  geom_point(mapping=aes(x=ro_km, y=prezzo)) +
  facet_wrap(~range_sup, nrow=3)

ggplot(data=df) + 
  geom_smooth(mapping=aes(x=ro_km, y=anno.di.costruzione, color=range_sup), se=F)

ggplot(data=df) + 
  geom_smooth(mapping=aes(x=ro_km, y=anno.di.costruzione)) + 
  geom_point(mapping=aes(x=ro_km, y=anno.di.costruzione)) +
  facet_wrap(~range_sup, nrow=3)

# è confermato che l'aumento di prezzo dovuto all'anno di costruzione è controbilanciato
# dalla diminuzione dovuta alla maggiore distanza dal centro

# emergono pattern interessanti come il fatto che grandi appartamenti oltre una certa
# distanza tornano ad essere vecchi, e entro il primo km ci sono più appartamenti nuovi
# che nella fascia centrale

# definiamo ora un framework per identificare appartamenti con prezzo più basso rispetto a quanto previsto
# da un modello: dopo aver modellizzato i dati, cerchiamo gli immobili con i residui più alti

# in questo esempio consideriamo un modello di regressione lineare multipla

model <- lm(prezzo ~ superficie + anno.di.costruzione, data=df)
summary(model)

model <- lm(prezzo ~ superficie + anno.di.costruzione, data=df)
summary(model)
par(mfrow=c(2, 2))
plot(model)

# anno di costruzione correla debolmente con prezzo, ma è significativo nella regressione
# seppure aggiunga una minima parte di varianza spiegata

res <- residuals(model)
underpriced <- res[res<0]
underpriced_sort <- sort(underpriced)
underpriced_sort <- df[names(underpriced_sort),] %>% filter(between(superficie, 60, 80))

# selezionamo gli appartamenti in una certa zona di interesse (e.g. Acquabella)

df_ab <- underpriced_sort %>% filter(between(lat, 45.46216, 45.46930)) %>% 
  filter(between(lon, 9.22259, 9.23481))
