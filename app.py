import streamlit as st
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

st.set_page_config(page_title="Slickdeals Live Deals Scraper", layout="wide")
st.title("Slickdeals Live Deals Scraper")

def get_debug_area():
    return st.expander("Debug Output", expanded=True)

def get_stealth_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }

# Category mapping
CATEGORY_URLS = {
    'Apple': 'https://slickdeals.net/deals/apple/',
    'Autos': 'https://slickdeals.net/deals/auto/',
    'Babies & Kids': 'https://slickdeals.net/deals/children/',
    'Bags & Luggage': 'https://slickdeals.net/deals/bags/',
    'Books & Magazines': 'https://slickdeals.net/deals/books-magazines/',
    'Computers': 'https://slickdeals.net/computer-deals/',
    'Education': 'https://slickdeals.net/deals/education/',
    'Finance': 'https://slickdeals.net/deals/finance/',
}

st.write("Select a category and number of pages to scrape.")
category = st.selectbox("Category", list(CATEGORY_URLS.keys()), index=0)
num_pages = st.number_input("Number of Pages", min_value=1, max_value=10, value=1, step=1)

if st.button("Scrape Slickdeals Live"):
    results = []
    debug_area = get_debug_area()
    with st.spinner(f"Scraping {category} deals from Slickdeals.net..."):
        try:
            options = uc.ChromeOptions()
            headers = get_stealth_headers()
            options.add_argument(f"--user-agent={headers['User-Agent']}")
            options.add_argument("--headless=new")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            driver = uc.Chrome(options=options)
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {"headers": headers})
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                """
            })
            base_url = CATEGORY_URLS[category]
            for page in range(1, num_pages + 1):
                url = base_url
                if not url.endswith('/'):
                    url += '/'
                url = f"{url}?page={page}"
                debug_area.write(f"Navigating to: {url}")
                driver.get(url)
                sleep_time = random.uniform(4, 7)
                debug_area.write(f"Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "bp-p-blueberryDealCard"))
                    )
                except Exception as e:
                    debug_area.write(f"Timeout waiting for deal cards on page {page}: {e}")
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                deal_cards = soup.find_all('li', class_='bp-p-blueberryDealCard')
                debug_area.write(f"Page {page}: Found {len(deal_cards)} deal cards.")
                for card in deal_cards:
                    title_tag = card.find('a', class_='bp-c-card_title')
                    title = title_tag.get_text(strip=True) if title_tag else ''
                    deal_link = f"https://slickdeals.net{title_tag['href']}" if title_tag and title_tag.has_attr('href') else ''
                    price_tag = card.find('span', class_='bp-p-dealCard_price')
                    price = price_tag.get_text(strip=True) if price_tag else ''
                    orig_price_tag = card.find('span', class_='bp-p-dealCard_originalPrice')
                    orig_price = orig_price_tag.get_text(strip=True) if orig_price_tag else ''
                    store_tag = card.find('span', class_='bp-c-card_subtitle')
                    store = store_tag.get_text(strip=True) if store_tag else ''
                    img_tag = card.find('a', class_='bp-c-card_imageContainer')
                    img = ''
                    if img_tag:
                        img_inner = img_tag.find('img')
                        if img_inner and img_inner.has_attr('data-lazy-src'):
                            img = f"https://slickdeals.net{img_inner['data-lazy-src']}"
                    found_by = card.find('div', class_='bp-p-blueberryDealCard_foundBy')
                    posted = ''
                    user = ''
                    if found_by:
                        time_tag = found_by.find('span', class_='bp-p-blueberryDealCard_timestamp')
                        posted = time_tag.get_text(strip=True) if time_tag else ''
                        user = found_by.get_text(strip=True).replace(posted, '').replace('by', '').strip() if posted else found_by.get_text(strip=True)
                    votes_tag = card.find('span', class_='bp-p-votingThumbsPopup_voteCount')
                    votes = votes_tag.get_text(strip=True) if votes_tag else ''
                    comments_tag = card.find('a', class_='bp-p-blueberryDealCard_comments')
                    comments = ''
                    if comments_tag:
                        try:
                            comments = int(comments_tag.get_text(strip=True))
                        except Exception:
                            comments = comments_tag.get_text(strip=True)
                    results.append({
                        'Title': title,
                        'Deal Link': deal_link,
                        'Price': price,
                        'Original Price': orig_price,
                        'Store': store,
                        'Image': img,
                        'Posted': posted,
                        'User': user,
                        'Votes': votes,
                        'Comments': comments,
                        'Page': page
                    })
            driver.quit()
        except Exception as e:
            st.error(f"Error occurred: {e}")
            debug_area.write(f"Exception: {e}")
            results = []
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"slickdeals_{category.lower().replace(' ', '_')}_deals_live.csv",
            mime="text/csv"
        )
    else:
        st.warning("No deals found on the live page.") 