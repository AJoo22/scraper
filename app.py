import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
import tempfile
import os

# Function to simulate infinite scrolling
async def scroll_to_bottom(page, scrolls=50, delay=1.5):
    for i in range(scrolls):
        await page.mouse.wheel(0, 5000)
        await asyncio.sleep(delay)

# Main scraping function
async def scrape_all_info(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle')

        await scroll_to_bottom(page, scrolls=50, delay=1.5)
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')

        product_blocks = soup.find_all('div', {'data-testid': 'product-card'})
        names, subtitles, prices, image_urls, product_links = [], [], [], [], []

        for product in product_blocks:
            names.append(product.find('div', class_='product-card__title').get_text(strip=True) if product.find('div', class_='product-card__title') else None)
            subtitles.append(product.find('div', class_='product-card__subtitle').get_text(strip=True) if product.find('div', class_='product-card__subtitle') else None)
            prices.append(product.find('div', {'data-testid': 'product-price'}).get_text(strip=True) if product.find('div', {'data-testid': 'product-price'}) else None)
            
            img_tag = product.find('a', {'data-testid': 'product-card__img-link-overlay'})
            if img_tag:
                img = img_tag.find('img')
                image_urls.append(img['src'] if img and img.get('src') else None)
            else:
                image_urls.append(None)

            link_tag = product.find('a', {'data-testid': 'product-card__link-overlay'})
            product_links.append(link_tag['href'] if link_tag and link_tag.get('href') else None)

        df = pd.DataFrame({
            'Name': names,
            'Subtitle': subtitles,
            'Price': prices,
            'Image URL': image_urls,
            'Product Link': product_links
        })

        return df

# Streamlit UI
st.title("Nike Product Scraper 🏟️")
url = st.text_input("Enter Nike Category URL:", "https://www.nike.com/lu/en/w/football-shoes-1gdj0zy7ok")

if st.button("Scrape Products"):
    with st.spinner("Scraping in progress... please wait ⏳"):
        df = asyncio.run(scrape_all_info(url))
        st.success(f"Scraped {len(df)} products!")

        st.dataframe(df)

        # Save CSV temporarily and allow download
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df.to_csv(tmp_file.name, index=False)
        with open(tmp_file.name, "rb") as f:
            st.download_button(
                label="📥 Download CSV",
                data=f,
                file_name="nike_products.csv",
                mime="text/csv"
            )
        os.unlink(tmp_file.name)
