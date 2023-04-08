# il modello di regressione lineare multipla fittato su poche variabili 
# determina grossi residui che possono essere spiegati aggiungendo più variabili
# al modello oppure scegliendo un diverso modello: la regressione lineare è 
# solitamente utile a investigare l'andamento generico di pattern 
# presenti nei dati senza troppe pretese di accuratezza della modellazione

# usiamo un modello tipo gradient boosting per un miglior risultato, e questa
# volta analizziamo i residui solo su un test set tenuto a parte (out-of-sample)
# spiegando al contempo la predizione con i valori SHAP

install.packages('devtools')
devtools::install_url('https://github.com/catboost/catboost/releases/download/v1.1.1/catboost-R-Darwin-1.1.1.tgz', INSTALL_opts = c("--no-multiarch", "--no-test-load"))

library(caret)

df <- read.csv("../immobiliare_ads_clean_2023-01-07.csv")

# training / test split

set.seed(2023)

prezzo <- df$prezzo
partition <- createDataPartition(y=prezzo, p=.9, list=F)
training <- df[partition,]
test <- df[-partition,]

dropped_cols <- c('descrizione', 'indirizzo', 'riferimento.e.data.annuncio', ...)
test_ids <- testing %>% select(dropped_cols)
test <- testing %>% select(-dropped_cols)
training <- training %>% select(-dropped_cols)
