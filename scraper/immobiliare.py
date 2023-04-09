"""
Implements the class to scrape real-estate ads from Immobiliare.it.
"""

from datetime import datetime as dt
import json
import os
import pandas as pd
import requests
from selenium import webdriver
import selenium.common.exceptions as se
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

        # user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        user_agent = 'Chrome/112.0.5615.49'
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument(f'user-agent={user_agent}')

        self._browser = webdriver.Chrome(options=options)
        self._browser.implicitly_wait(5)
        return

    @staticmethod
    def _list_to_dict(input_list):
        output_dict = {input_list[i].lower(): input_list[i+1] for i in range(0, len(input_list), 2)}
        return output_dict

    def _scrape_ad(self, url):
        """Scrape a single ad."""

        self._browser.get(self._url)
        dict_list = []

        try:
            description = self._browser.find_elements(By.XPATH, "//div[contains(@class, 'readAllContainer')]").text
        except se.NoSuchElementException:
            description = ""

        try:
            items = self._browser.find_elements(By.XPATH, "//div[contains(@class, 'im-map__description')]//span//span")
            address = "Milano, " + items[2].text
        except (se.NoSuchElementException, IndexError):
            address = None

        lat = None
        lon = None
        if address is not None:
            osm_url = 'https://nominatim.openstreetmap.org/search?q={}&format=json'.format(address)
            response = requests.request("GET", osm_url)
            if response.text == '[]':
                pass
            else:
                try:
                    j = json.loads(response.text)[0]
                    lat = j['lat']
                    lon = j['lon']
                except json.decoder.JSONDecodeError:
                    pass

        dict_list.append("descrizione")
        dict_list.append(description)
        dict_list.append("indirizzo")
        dict_list.append(address)
        dict_list.append("lat")
        dict_list.append(lat)
        dict_list.append("lon")
        dict_list.append(lon)

        desc_list = self._browser.find_elements(By.TAG_NAME, "dl")
        for desc in desc_list:
            children = desc.find_elements(By.XPATH, ".//*")
            for child in children:
                if child.tag_name in ['dt', 'dd']:
                    dict_list.append(child.text)

        return self._list_to_dict(dict_list)

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
