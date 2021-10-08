from datetime import datetime as dt
import pandas as pd
import re
from selenium import webdriver
import selenium.common.exceptions as se
from tqdm import tqdm

# scrape agency and services around the place

def list_to_dict(input_list):
    output_dict = {input_list[i]: input_list[i + 1] for i in range(0, len(input_list), 2)}
    return output_dict


def scrape_ad(url):
    browser.get(url)
    dict_list = []
    try:
        description = browser.find_element_by_xpath("//div[contains(@class, 'description-text')]").text
    except se.NoSuchElementException:
        description = ""
    try:
        address = browser.find_element_by_xpath("//span[contains(@class, 'im-address')]").get_attribute("innerText")
        address = address.encode("ascii", "replace").decode("utf-8")
        address = address.replace("\n", " ").replace("?", " ")
        address = re.sub("\s+", " ", address).strip()
    except se.NoSuchElementException:
        address = None
    try:
        coord = browser.find_element_by_xpath("//div[contains(@class, 'image-placeholder')]").get_attribute(
                                                                                              'data-background-image')
        coord = re.findall("\d+\.\d+", coord)[:2]
    except se.NoSuchElementException:
        coord = [None, None]
    dict_list.append("DESCRIZIONE")
    dict_list.append(description)
    dict_list.append("INDIRIZZO")
    dict_list.append(address)
    dict_list.append("LAT")
    dict_list.append(coord[0])
    dict_list.append("LONG")
    dict_list.append(coord[1])
    desc_list = browser.find_elements_by_tag_name("dl")
    for desc in desc_list:
        children = desc.find_elements_by_xpath(".//*")
        for child in children:
            if child.tag_name in ['dt', 'dd']:
                dict_list.append(child.text)
    items = browser.find_elements_by_xpath('.//div[h3/text() = "Caratteristiche"]/div/span')
    char = ";".join([item.text for item in items])
    dict_list.append("CARATTERISTICHE")
    dict_list.append(char)
    return list_to_dict(dict_list)


def get_ids():
    # set with unique ad ids
    ads_df = pd.DataFrame()
    # page id
    page_id = 1
    print("Retrieving ads list...")
    while True:
        print("Fetching from page {}".format(page_id), end="")
        browser.get(start_url.format(page_id))
        if "404 Not Found" in browser.title:
            break
        links = browser.find_elements_by_class_name("in-card__title")
        titles = [elem.get_attribute('title') for elem in links]
        urls = [elem.get_attribute('href') for elem in links]
        ads_df = ads_df.append({'url': urls, 'titolo': titles}, ignore_index=True)
        page_id += 1
        print("\r", end="")
    print("\nFound {} ads".format(len(ads_df)))
    output_file = 'immobiliare_ids_{}.csv'.format(dt.today().strftime('%Y-%m-%d'))
    ads_df.to_csv(output_file)
    print("Saved ids to {}".format(output_file))
    return output_file


def save_ckpt(lots):
    lots_df = pd.DataFrame(lots)
    lots_df.to_csv("immobiliare_ads_ckpt.csv")
    return lots_df


def get_ads(ids_file, checkpoint=100):
    ads_df = pd.read_csv(ids_file)
    print("Loaded ids from {}".format(ids_file))
    # lots dictionaries
    lots = []
    print("Scraping ads...")
    for it, row in tqdm(ads_df.iterrows(), total=len(ads_df)):
        if it % checkpoint == 0 and it > 0:
            save_ckpt(lots)
        ad_url_it = ad_url.format(row['DATA-ID'])
        lot = scrape_ad(ad_url_it)
        lots.append(lot)
    output_file = 'immobiliare_ads_{}.csv'.format(dt.today().strftime('%Y-%m-%d'))
    lots_df = save_ckpt(lots)
    ads_df = ads_df.merge(lots_df, right_index=True, left_index=True)
    ads_df.to_csv(output_file)
    # os.remove("immobiliare_ads_ckpt.csv")
    # os.remove(ids_file) REMOVE IDS?
    # close the driver
    browser.quit()


# driver options
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
options = webdriver.ChromeOptions()
# options.add_argument('headless')
options.add_argument(f'user-agent={user_agent}')

# create a new driver
browser = webdriver.Chrome(options=options)
browser.implicitly_wait(5)

# urls to be scraped
start_url = 'https://www.immobiliare.it/vendita-case/milano/?pag={}'
ad_url = 'https://www.immobiliare.it/annunci/{}'

if __name__ == "__main__":
    # scrape_ad("https://www.immobiliare.it/annunci/79095919/")
    ids_file = get_ids()
    # get_ads(ids_file)
