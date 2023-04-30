# Real Estate

The goal is to scrape ads of apartments for sale in Milan, discover and 
describe interesting patterns within them, and model the data to predict
and explain the price of any apartment

## Code structure

* scraper
  * immobiliare.py _implements the scraper class for immobiliare.it_
* analytics
  * data_exploration.R _script for EDA_
* utils
  * data_preparation.R _function to preprocess the data_

## Setup

Run `source.sh` to setup the Python virtualenv environment with the needed requirements.
R is also needed for data exploration and analysis