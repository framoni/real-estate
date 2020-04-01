# Title: Real Estate Estimate Feature Selection
# Objective: Select features to predict prices for houses in Milan, modeling the data scraped from immobiliare.it
# Created by: Francesco Ramoni
# Created on: 07/02/2020

library(caret)
library(corrplot)
library(dplyr)
library(ggmap)
library(ggplot2)
library(Metrics)
library(plotly)
library(randomForest)
library(SHAPforxgboost)
library(xgboost)

#----------------------------------------------------------------------------------------------------------------------#
# Experiments

# only SUPERFICIE: lr 0.55, rf 0.58, xgb needs more features
# SUP, LAT, LONG: lr 0.55, rf 0.38, xgb 0.33, SUP > LAT > LONG
# SUP, LAT, LONG, ANNO: lr 0.55, rf 0.37, xgb 0.37 SUP > LAT > LONG > ANNO

# take only "Appartamento":

# SUP, LAT, LONG: lr 0.49, rf 0.27, xgb 0.228, SUP > LAT > LONG

# SUP, LAT, LONG, ANNO: lr 0.488, rf 0.269, xgb 0.224 SUP > LAT > LONG > ANNO
# SUP, LAT, LONG, ANNO, STATO: lr 0.479, rf 0.38, xgb 0.215 SUP > LAT > LONG > ANNO > STATO
# SUP, LAT, LONG, ANNO, STATO, RISCALD: lr 0.479, rf 0.33, xgb 0.213 SUP > LAT > LONG > ANNO > STATO > RISCALD
# SUP, LAT, LONG, ANNO, STATO, RISCALD, CE: rf 0.24, xgb 0.204 SUP > LAT > LONG > ANNO > STATO > CE > RISCALD
# SUP, LAT, LONG, ANNO, STATO, RISCALD, CE, CONDIZ: rf 0.25, xgb 0.204 SUP > LAT > LONG > ANNO > STATO > CONDIZ > CE > RISCALD
# SUP, LAT, LONG, ANNO, STATO, RISCALD, CE, CONDIZ, TOT_STANZE: rf 0.25, xgb 0.200 SUP > LAT > LONG > TOT_STANZE > ANNO > STATO > CONDIZ > CE > RISCALD
# SUP, LAT, LONG, ANNO, STATO, RISCALD, CE, CONDIZ, TOT_STANZE, BOX: rf 0.237, xgb 0.200 SUP > LAT > LONG > TOT_STANZE > ANNO > STATO > CONDIZ > CE > BOX > RISCALD
# add "PIANO": about same performances
# add "DELTA_PIANO": rf 0.247, xgb 0.188
# add "ASCENSORE": rf 0.238, xgb 0.187
# add "TIPO PROPRIETÀ" rf 0.230, xgb 0.173, feature is important!

# "POSTO AUTO" is useless

# load dataframe

df <- read.csv("immobiliare_ads_clean_2020-03-03.csv")
head(df)

df <- df[df$TIPOLOGIA == "Appartamento", ]

df <- df[df$DELTA_PIANO >= -1, ]

df <- select(df, c(DATA.ID, TITOLO, PREZZO, LAT, LONG, SUPERFICIE, ANNO.DI.COSTRUZIONE, STATO, RISCALDAMENTO,
                   CLASSE.ENERGETICA, CONDIZIONATORE, CUCINE, CAMERE_LETTO, ALTRO, BAGNI, BOX, PIANO, DELTA_PIANO, ASCENSORE, TIPO.PROPRIETÀ, 
                   camino, porta.blindata, cantina, numero.vetri, mat.legno, mat.pvc, mat.al, arredo, portiere, impianto.tv, giardino, 
                   esposizione.interna, esposizione.esterna, esposizione.doppia, balcone, terrazza, piscina, idromassaggio, 
                   impianto.allarme, mansarda, cancello.elettrico, fibra.ottica, taverna, campo.da.tennis, videocitofono))

#----------------------------------------------------------------------------------------------------------------------#

# partitioning

set.seed(2020)

prezzo <- df$PREZZO
partition <- createDataPartition(y=prezzo, p=.9, list=F)
training <- df[partition,]
testing <- df[-partition,]

drop.cols <- c('DATA.ID', 'TITOLO')
testing_ids <- testing %>% select(drop.cols)
testing <- testing %>% select(-drop.cols)
training <- training %>% select(-drop.cols)

#----------------------------------------------------------------------------------------------------------------------#

# one hot encoding

dummies <- dummyVars(" ~ .", data = training)
training <- data.frame(predict(dummies, newdata = training))
testing <- data.frame(predict(dummies, newdata = testing))

#----------------------------------------------------------------------------------------------------------------------#

# correlations

correlations <- cor(training, use="everything")
corrplot(correlations, method="circle", type="lower", sig.level = 0.01, insig = "blank")

#----------------------------------------------------------------------------------------------------------------------#

# linear regression model

rm <- lm(log(PREZZO) ~ ., data=training)
summary(rm)

# predict and evaluate on test set

pred <- predict(rm, testing, type="response")

rmse(log(testing$PREZZO), pred)

#----------------------------------------------------------------------------------------------------------------------#

# random forest

rf <- randomForest(PREZZO ~ ., data=training, importance=T)

# predict and evaluate on test set

pred <- predict(rf, testing)

rmse(log(testing$PREZZO), log(pred))

importance(rf)

#----------------------------------------------------------------------------------------------------------------------#

# gradient boosting

# create matrices from the data frames

trainData <- as.matrix(training, rownames.force=NA)
testData <- as.matrix(testing, rownames.force=NA)

# turn the matrices into sparse matrices

train2 <- as(trainData, "sparseMatrix")
test2 <- as(testData, "sparseMatrix")

vars <- 2:ncol(training) # exclude price

trainD <- xgb.DMatrix(data = train2[, vars], label = log(train2[,"PREZZO"])) # Convert to xgb.DMatrix format

# choose the parameters for the model

param <- list(colsample_bytree = .7,
             subsample = .7,
             booster = "gbtree",
             max_depth = 10,
             eta = 0.02,
             eval_metric = "rmse",
             objective="reg:linear")

# train the model using those parameters

bstSparse <- xgb.train(params = param,
                       data = trainD,
                       nrounds = 1500,
                       watchlist = list(train = trainD),
                       verbose = TRUE,
                       print_every_n = 50,
                       nthread = 2)

# # save the model
#
# saveRDS(bstSparse, file="XGB_2020-02-18.rds")
#
# # load the model
#
# bstSparse <- readRDS(file="XGB_2020-02-18.rds")

testD <- xgb.DMatrix(data = test2[, vars])

pred <- predict(bstSparse, testD)

# put testing prediction and test dataset all together

test3 <- as.data.frame(as.matrix(test2))
pred <- as.data.frame(as.matrix(pred))
colnames(pred) <- "predicted"
model_output <- cbind(test3, pred)

model_output_pos <- subset(model_output, predicted > 0)
model_output_pos$log_prediction <- model_output_pos$predicted
model_output_pos$log_PREZZO <- log(model_output_pos$PREZZO)

# test with RMSE

logrmse <- rmse(model_output_pos$log_PREZZO, model_output_pos$log_prediction)

# feature importance

xgb.importance(model = bstSparse)

#----------------------------------------------------------------------------------------------------------------------#

training <- df

drop.cols <- c('DATA.ID', 'TITOLO')
training_ids <- training %>% select(drop.cols)
training <- training %>% select(-drop.cols)

# one hot encoding

dummies <- dummyVars(" ~ .", data = training)
training <- data.frame(predict(dummies, newdata = training))

# choose the parameters for the model

param <- list(colsample_bytree = .7,
              subsample = .7,
              booster = "gbtree",
              max_depth = 10,
              eta = 0.02,
              eval_metric = "rmse",
              objective="reg:linear")

trainData <- as.matrix(training, rownames.force=NA)
train2 <- as(trainData, "sparseMatrix")
vars <- 2:ncol(training) # exclude price
trainD <- xgb.DMatrix(data = train2[, vars], label = log(train2[,"PREZZO"])) # Convert to xgb.DMatrix format

cv <- xgb.cv(params = param, data = trainD, 1500, nfold = 4, label = NULL, missing = NA,
       prediction = TRUE, showsd = TRUE, metrics = list("rmse"), obj = NULL,
       feval = NULL, stratified = TRUE, folds = NULL, verbose = TRUE,
       print_every_n = 100, early_stopping_rounds = NULL, maximize = NULL)

#----------------------------------------------------------------------------------------------------------------------#

# SHAP values debugging

shap_values <- shap.values(xgb_model = bstSparse, X_train = trainData[, vars])
shap_long <- shap.prep(xgb_model = bstSparse, X_train = trainData[, vars])
shap.plot.summary(shap_long)
which(testing_ids$data.id == 76824158) # good prediction
which(testing_ids$data.id == 78241489) # overestimating by 300k
shap_values$shap_score[207,]

#----------------------------------------------------------------------------------------------------------------------#

# # gradient boosting parameter search
#
# # set up the cross-validated hyper-parameter search
# xgb_grid_1 <- expand.grid(
# nrounds = 1000,
# eta = c(0.01, 0.001, 0.0001),
# max_depth = c(2, 4, 6, 8, 10),
# gamma = 1
# )
#
# # pack the training control parameters
# xgb_trcontrol_1 <- trainControl(
# method = "cv",
# number = 5,
# verboseIter = TRUE,
# returnData = FALSE,
# returnResamp = "all", # save losses across all models
# classProbs = TRUE, # set to TRUE for AUC to be computed
# summaryFunction = twoClassSummary,
# allowParallel = TRUE
# )
#
# # train the model for each parameter combination in the grid,
# # using CV to evaluate
# xgb_train_1 = train(
# x = as.matrix(df_train %>%
# select(-SeriousDlqin2yrs)),
# y = as.factor(df_train$SeriousDlqin2yrs),
# trControl = xgb_trcontrol_1,
# tuneGrid = xgb_grid_1,
# method = "xgbTree"
# )
#
# # scatter plot of the AUC against max_depth and eta
# ggplot(xgb_train_1$results, aes(x = as.factor(eta), y = max_depth, size = ROC, color = ROC)) +
# geom_point() +
# theme_bw() +
# scale_size_continuous(guide = "none")

#----------------------------------------------------------------------------------------------------------------------#

# scatter plot of testing predictions

plot_name <- "scatterplot_testing_XGBOOST_Appartamento_2020-03-03.html"

pred_df <- data.frame(actual=testing$PREZZO, predicted=exp(pred), title=testing_ids$TITOLO, id=testing_ids$DATA.ID)
p <- ggplot(pred_df, aes(x=actual, y=predicted)) +
     geom_point(size=2, colour="slateblue1", aes(label=id, text=title)) +
     geom_line(aes(y = actual), size = 1, color="lightcoral") +
     geom_segment(aes(xend = actual, yend = actual)) + ggtitle(paste("CV: ACTUAL VS PREDICTED"))
p <- ggplotly(p)
htmlwidgets::saveWidget(as_widget(p), plot_name)

# plot the points on a map of Milan

lat <- df$LAT / 1000 + 45.46425
long <- df$LONG / 1000 + 9.1887274
df$LONG = long
df$LAT = lat
df$SET[partition] = "TRAINING"
df$SET[-partition] = "TEST"

# make it plot ad title and price too

register_google(key="AIzaSyANpUyX1htd6qSf4GAir7As7QYtozWYRFo")
map <- qmplot(LONG, LAT, data = df, label = title, colour = SET, size = PREZZO, maptype = "roadmap",
              source = "google", main = "LOCATION OF HOUSES FOR SALE IN MILAN")
p <- ggplotly(map)
htmlwidgets::saveWidget(as_widget(p), "map_2020-02-18.html")
