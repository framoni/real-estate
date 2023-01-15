from datetime import datetime as dt
import json
import os
import pandas as pd
import requests
from selenium import webdriver
import selenium.common.exceptions as se
from tqdm import tqdm

# scrape agency and services around the place


def is_duplicate(prev_ads_df, lot):
    # future: use address, area, floor
    if prev_ads_df is None:
        return False
    match_df = prev_ads_df[(prev_ads_df['titolo'] == lot['titolo']) | (prev_ads_df['descrizione'] == lot['descrizione'])]
    if len(match_df) > 0:
        if match_df.iloc[0]['prezzo'] == lot['prezzo']:
            return True
    else:
        return False


def list_to_dict(input_list):
    output_dict = {input_list[i].lower(): input_list[i+1] for i in range(0, len(input_list), 2)}
    return output_dict


def scrape_ad(url):
    browser.get(url)
    dict_list = []

    try:
        description = browser.find_element_by_xpath("//div[contains(@class, 'readAllContainer')]").text
    except se.NoSuchElementException:
        description = ""

    try:
        items = browser.find_elements_by_xpath("//div[contains(@class, 'im-map__description')]//span//span")
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

    desc_list = browser.find_elements_by_tag_name("dl")
    for desc in desc_list:
        children = desc.find_elements_by_xpath(".//*")
        for child in children:
            if child.tag_name in ['dt', 'dd']:
                dict_list.append(child.text)
    return list_to_dict(dict_list)


def get_ids():
    """Get the ids of the currently available ads."""
    ads_df = pd.DataFrame()
    page_id = 1
    print("Retrieving ads list...")
    while True:
        print("Fetching from page {}".format(page_id), end="")
        browser.get(start_url.format(page_id))
        links = browser.find_elements_by_class_name("in-card__title")
        if len(links) == 0:
            break
        titles = [elem.get_attribute('title') for elem in links]
        urls = [elem.get_attribute('href') for elem in links]
        ads_df = ads_df.append(pd.DataFrame({'url': urls, 'titolo': titles}).dropna(), ignore_index=True)
        page_id += 1
        print("\r", end="")
    print("\nFound {} ads".format(len(ads_df)))
    return ads_df


def get_ads(ads_df, date):
    """Scrape ads and save the relative dataframe."""
    output_file = 'immobiliare_ads_{}.csv'.format(date)
    lots = []
    print("Scraping ads...")
    for it, row in tqdm(ads_df.iterrows(), total=len(ads_df)):
        lot = scrape_ad(row['url'])
        lot['url'] = row['url']
        lot['titolo'] = row['titolo']
        lot['data'] = date
        lots.append(lot)
    ads_df = pd.DataFrame(lots)
    ads_df.to_csv(output_file, index=False)
    browser.quit()


# driver options
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument(f'user-agent={user_agent}')

# create a new driver
browser = webdriver.Chrome(options=options)
browser.implicitly_wait(5)

# urls to be scraped
start_url = 'https://www.immobiliare.it/vendita-case/milano/?pag={}'

if __name__ == "__main__":
    date = dt.today().strftime('%Y-%m-%d')
    ads_df = get_ids()
    get_ads(ads_df, date)
