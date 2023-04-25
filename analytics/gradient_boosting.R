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
library(catboost)
library(tidyr)

df <- read.csv("data/immobiliare_ads_2023-04-10_10:54:33.csv")

# prepare data

source('utils/data_preparation.R')

df <- immobiliare_prep(df)

df <- drop_na(df, price, latitude, longitude, buildingYear, rooms, bathrooms, 
              bedRoomsNumber, hasElevators, surface, floors, floor, condoExpenses, class)

# replace all other columns NAs with zeros

df <- replace_na(df, 0)

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

###

target = c("price")
# x <- df[, !(names(df) %in% target)]
x <- df[, c('latitude', 'longitude')]
y <- df[, target]

fit_control <- trainControl(method = "cv",
                            number = 5,
                            classProbs = TRUE)

report <- train(x, as.factor(make.names(y)),
                method = catboost.caret,
                logging_level = 'Verbose', preProc = NULL,
                trControl = fit_control)


print(report)

importance <- varImp(report, scale = FALSE)
print(importance)