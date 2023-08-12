"""
Implements the class to scrape real-estate ads from Immobiliare.it.
"""

from bs4 import BeautifulSoup
from datetime import datetime as dt
import json
import os
import pandas as pd
import requests
from tqdm import tqdm


class Immobiliare:

    def __init__(self, path='../data', places=['milano']):
        self.date = dt.today().strftime('%Y-%m-%d_%H:%M:%S')
        self._ids = None
        self.ads = None
        self._places = places
        self._url = 'https://www.immobiliare.it/vendita-case/{}/?pag={}'
        self._path = path

    @staticmethod
    def _parse_field(dict_, field):
        try:
            if type(field) == str:
                value = dict_[field]
            else:
                value = dict_[field[0]][field[1]]
        except KeyError:
            return
        except TypeError:
            return
        return value

    def _parse_dict(self, ad_dict):
        """Parse useful information from the ad's JSON."""
        lot = {}

        try:
            ad_dict = ad_dict['props']['pageProps']['detailData']['realEstate']
        except KeyError:
            return lot

        for field in ['id', 'createdAt', 'updatedAt', 'contract']:
            lot[field] = self._parse_field(ad_dict, field)

        lot['price'] = self._parse_field(ad_dict, ['price', 'value'])
        lot['typology'] = self._parse_field(ad_dict, ['typology', 'name'])

        prop_dict = self._parse_field(ad_dict, ['properties', 0])

        for field in ['availability', 'condition', 'buildingYear',  'rooms', 'bathrooms', 'bedRoomsNumber',
                      'hasElevators', 'surface', 'floors', 'garage']:
            lot[field] = self._parse_field(prop_dict, field)

        lot['floor'] = self._parse_field(prop_dict, ['floor', 'abbreviation'])

        lot['category'] = self._parse_field(prop_dict, ['category', 'name'])

        lot['condoExpenses'] = self._parse_field(prop_dict, ['costs', 'condominiumExpenses'])
        lot['expenses'] = self._parse_field(prop_dict, ['costs', 'expenses'])

        lot['heatingType'] = self._parse_field(prop_dict, ['energy', 'heatingType'])
        lot['airConditioning'] = self._parse_field(prop_dict, ['energy', 'airConditioning'])
        lot['class'] = self._parse_field(prop_dict, ['energy', 'class'])

        lot['latitude'] = self._parse_field(prop_dict, ['location', 'latitude'])
        lot['longitude'] = self._parse_field(prop_dict, ['location', 'longitude'])

        if self._parse_field(prop_dict, 'features') is not None:
            for feature in prop_dict['features']:
                lot[feature] = 1

        return lot

    def _scrape_ad(self, url):
        """Scrape a single ad."""
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        ad_dict = json.loads(soup.find(id="__NEXT_DATA__").text)
        return self._parse_dict(ad_dict)

    def _get_ids(self):
        """Get the ids of the currently available ads."""
        ids_df = pd.DataFrame()
        print("Retrieving ads list...")
        for place in self._places:
            page_id = 1
            while True:
                print("Fetching ads in {} from page {}".format(place, page_id), end="")
                page = requests.get(self._url.format(place, page_id))
                soup = BeautifulSoup(page.content, "html.parser")
                links = soup.find_all("a", "in-card__title")
                if len(links) == 0:
                    print('')
                    break
                titles = [it['title'] for it in links]
                urls = [it['href'] for it in links]
                ids_df = pd.concat([ids_df, pd.DataFrame({'url': urls, 'titolo': titles}).dropna()], ignore_index=True)
                page_id += 1
                print("\r", end="")
        print("Found {} ads".format(len(ids_df)))
        return ids_df

    def _get_ads(self):
        """Scrape ads into a dataframe."""
        lots = []
        print("Scraping ads...")
        for it, row in tqdm(self._ids.iterrows(), total=len(self._ids)):
            lot = self._scrape_ad(row['url'])
            lot['url'] = row['url']
            lot['titolo'] = row['titolo']
            lots.append(lot)
        ads_df = pd.DataFrame(lots)
        return ads_df

    def run(self):
        """Run the scraper."""
        # self._init_browser()
        if self._ids is None:
            self._ids = self._get_ids()
        self.ads = self._get_ads()
        filename = 'immobiliare_ads_{}_{}.csv'.format('_'.join(self._places), self.date)
        self.ads.to_csv(os.path.join(self._path, filename), index=False)


if __name__ == "__main__":
    scraper = Immobiliare(places=['Cambiasca', 'Vignone', 'Bee', 'Arizzano', 'Premeno'])
    scraper.run()
