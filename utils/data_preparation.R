# functions to prepare real-estate ads data

library(dplyr)
library(stringr)

immobiliare_prep <- function(df) {
  #TODO: handle missing values
  #TODO: check if there are repeating features
  
  # consider only real-estate for sale, and flats (TODO: also remove auctions)
  df <- df %>% filter(contract=='sale', typology=='Appartamento')
  
  # consider only flats that are not currently occupied
  df <- df %>% mutate(availability=tolower(availability)) %>%
    filter(availability=='libero')
  
  # drop columns not used for the modeling
  dropped_cols <- c(
                    'id', 
                    'createdAt', 
                    'updatedAt',
                    'contract',
                    'typology',
                    'availability',
                    'category',
                    'expenses',
                    'url',
                    'titolo'
                    )
  df <- df %>% select(-all_of(dropped_cols))
  
  # fill in empty values where it's reasonable to do so
  df$condition <- replace(df$condition, df$condition=="", "Buono / Abitabile")
  df$hasElevators <- replace(df$hasElevators, df$hasElevators=="", "False")

  # transform garage: 1 column for # boxes, one for # parking
  parse_garage <- function(x, type) {
    ans = str_match(x, paste("\\b(\\d+)\\s+in ", type , "\\b", sep=""))[,2]
    return(ifelse(is.na(ans), 0, strtoi(ans)))
  }
  
  df$box <- as.numeric(lapply(df$garage, function(x) parse_garage(x, 'box')))
  df$parking <- as.numeric(lapply(df$garage, function(x) parse_garage(x, 'parcheggio')))
  
  df <- df %>% select(-garage)
  
  # factorize categorical variables
  # cat_cols <- c(
  #               'condition',
  #               'hasElevators',
  #               'garage',
  #               'heatingType',
  #               'airConditioning',
  #               'class',
  #               df %>% select(longitude:last_col(), -longitude) %>% colnames() # all the columns after "longitude"
  #               )
  # df[cat_cols] <- apply(df[cat_cols], factor)
  
  # format surface, floors, condominium expenses
  df$surface <- str_extract(df$surface, "\\d+")
  df$floors <- str_extract(df$floors, "\\d+")
  df$condoExpenses <- str_extract(df$condoExpenses, "\\d+")

  # format floor
  df$floor[df$floor=='S'] <- '-0.5'
  df$floor[df$floor=='S3'] <- '-0.5'
  df$floor[df$floor=='S - T'] <- '0'
  df$floor[df$floor=='T'] <- '0'
  df$floor[df$floor=='T - R'] <- '0.5'
  df$floor[df$floor=='R'] <- '0.5'
  df$floor[df$floor=='3 - 4'] <- '3.5'
  df$floor[df$floor=='4 - 5'] <- '4.5'
  df$floor[df$floor=='8 - 9'] <- '8.5'
  
  # one-hot encode categorical variables
  one_hot_cols <- c(
                    'condition',
                    'heatingType',
                    'airConditioning'
  )
  dummy <- dummyVars(" ~ .", data=df[, one_hot_cols])
  df_one_hot <- data.frame(predict(dummy, newdata=df[, one_hot_cols]))
  # df_one_hot <- replace_na(df_one_hot, 0) # "condition" likely needs a different treatment
  df <- df %>% select(-all_of(one_hot_cols))
  df <- cbind(df, df_one_hot)
  
  # missing values
  df$bedRoomsNumber <- replace_na(df$bedRoomsNumber, 0)
  
  #fill_zeros <- df %>% select(longitude:last_col(), -longitude) %>% colnames()
  #df[fill_zeros] <- df[fill_zeros] %>% mutate(
  #  across(everything(), ~replace_na(.x, 0))
  #)
  
  # replace(is.na(.), 0)
  
  return(df)
}

df <- read.csv("data/immobiliare_ads_2023-04-10_10:54:33.csv")
df2 <- immobiliare_prep(df)
