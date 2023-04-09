"""
Implements the class to scrape real-estate ads from Immobiliare.it.
"""

from datetime import datetime as dt
import json
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm


class Immobiliare:

    def __init__(self, path='data'):
        self.date = dt.today().strftime('%Y-%m-%d_%H:%M:%S')
        self._browser = None
        self._ids = None
        self.ads = None
        self._url = 'https://www.immobiliare.it/vendita-case/milano/?pag={}'
        self._path = path

    def _init_browser(self):
        """Initialise a Chrome webdriver for scraping."""
        user_agent = 'Chrome/112.0.5615.49'
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument(f'user-agent={user_agent}')
        self._browser = webdriver.Chrome(options=options)
        self._browser.implicitly_wait(5)
        return

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
        self._browser.get(url)
        ad_dict = json.loads(self._browser.find_element(By.ID, "__NEXT_DATA__").get_attribute('innerHTML'))
        return self._parse_dict(ad_dict)

    def _get_ids(self):
        """Get the ids of the currently available ads."""
        ids_df = pd.DataFrame()
        page_id = 1
        print("Retrieving ads list...")
        while True:
            print("Fetching from page {}".format(page_id), end="")
            self._browser.get(self._url.format(page_id))
            links = self._browser.find_elements(By.CLASS_NAME, "in-card__title")
            if len(links) == 0:
                break
            titles = [elem.get_attribute('title') for elem in links]
            urls = [elem.get_attribute('href') for elem in links]
            ids_df = pd.concat([ids_df, pd.DataFrame({'url': urls, 'titolo': titles}).dropna()], ignore_index=True)
            page_id += 1
            print("\r", end="")
        print("\nFound {} ads".format(len(ids_df)))
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
        self._init_browser()
        if self._ids is None:
            self._ids = self._get_ids()
        self.ads = self._get_ads()
        filename = 'immobiliare_ads_{}.csv'.format(self.date)
        self.ads.to_csv(os.path.join(self._path, filename))
        self._browser.quit()


if __name__ == "__main__":
    scraper = Immobiliare()
    scraper.run()
