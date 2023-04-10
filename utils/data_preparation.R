# functions to prepare real-estate ads data

library(dplyr)
library(stringr)

immobiliare_prep <- function(df) {
  #TODO: handle missing values
  #TODO: check if there are repeating features
  
  # consider only real-estate for sale, and flats
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
  
  # factorize categorical variables
  cat_cols <- c(
                'condition',
                'hasElevators',
                'garage',
                'heatingType',
                'airConditioning',
                'class',
                df %>% select(longitude:last_col(), -longitude) %>% colnames() # all the columns after "longitude"
                )
  df[cat_cols] <- lapply(df[cat_cols], as.factor())
  
  # format surface, floors, condominium expenses
  df$surface <- str_extract(df$surface, "\\d+")
  df$floors <- str_extract(df$floors, "\\d+")
  df$floors <- str_extract(df$condoExpenses, "\\d+")

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
  
  return(df)
}

df <- read.csv("data/immobiliare_ads_2023-04-10_10:54:33.csv")
df2 <- immobiliare_prep(df)
