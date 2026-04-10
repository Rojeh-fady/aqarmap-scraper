from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import os
import re
import time

BASE_URL = "https://aqarmap.com.eg/en/for-sale/apartment/cairo/nasr-city/?location=cairo/nasr-city"

def clean_text(text):
    return " ".join(text.split()).strip()

def extract_price_and_price_per_meter(card):
    price = ""
    price_per_meter = ""

    try:
        raw_text = clean_text(card.text)
        # يجيب أول رقم كبير متبوع بـ EGP
        price_match = re.search(r"([\d,]+)\s*EGP", raw_text)
        if price_match:
            price = price_match.group(1) + " EGP"

        # يجيب سعر المتر
        ppm_match = re.search(r"([\d,]+)\s*EGP/m²", raw_text)
        if ppm_match:
            price_per_meter = ppm_match.group(1) + " EGP/m²"

    except:
        pass

    return price, price_per_meter

def extract_location(card):
    city = ""
    street = ""

    try:
        location_el = card.find_element(By.CSS_SELECTOR, "div.text-caption-1.text-gray__dark_2")
        location_text = clean_text(location_el.text)

        if "/" in location_text:
            parts = [p.strip() for p in location_text.split("/", 1)]
            city = parts[0]
            street = parts[1]
        else:
            street = location_text

    except:
        pass

    return city, street

def extract_title(card):
    try:
        title = clean_text(card.find_element(By.CSS_SELECTOR, "h2").text)
        return title
    except:
        return ""

def extract_link(card):
    try:
        links = card.find_elements(By.CSS_SELECTOR, "a")
        for a in links:
            href = a.get_attribute("href")
            if href and "/listing/" in href:
                return href
    except:
        pass
    return ""

def extract_details(card):
    area = ""
    bedrooms = ""
    bathrooms = ""

    try:
        items = card.find_elements(By.CSS_SELECTOR, "ul.flex.items-center.gap-x-2x.list-none > li")

        for item in items:
            try:
                text = clean_text(item.text)
            except:
                text = ""

            try:
                icon_class = item.find_element(By.TAG_NAME, "i").get_attribute("class")
            except:
                icon_class = ""

            if "m²" in text:
                area = text
            elif "bedroom-icon" in icon_class:
                bedrooms = text
            elif "bathroom-icon" in icon_class:
                bathrooms = text

    except:
        pass

    return area, bedrooms, bathrooms

def scrape_page(driver, url):
    driver.get(url)

    wait = WebDriverWait(driver, 25)
    cards = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.listing-card"))
    )

    time.sleep(2)

    properties_details = []

    for card in cards:
        try:
            title = extract_title(card)
            price, price_per_meter = extract_price_and_price_per_meter(card)
            city, street = extract_location(card)
            area, bedrooms, bathrooms = extract_details(card)
            link = extract_link(card)

            if title or price or street or area:
                properties_details.append({
                    "عنوان العقار": title,
                    "السعر": price,
                    "سعر المتر": price_per_meter,
                    "المدينة": city,
                    "الشارع": street,
                    "المساحة": area,
                    "غرف النوم": bedrooms,
                    "الحمامات": bathrooms,
                    "الرابط": link
                })

        except Exception as e:
            print("Error in card:", e)
            continue

    return properties_details

def main():
    driver = webdriver.Chrome()
    all_data = []
    seen_links = set()

    for page_num in range(1, 9):  # من 1 لـ 8
        if page_num == 1:
            url = BASE_URL
        else:
            url = BASE_URL + f"&page={page_num}"

        print(f"📄 بيجيب الصفحة {page_num}...")

        try:
            data = scrape_page(driver, url)

            # منع التكرار
            for row in data:
                link = row.get("الرابط", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_data.append(row)

            print(f"   ✅ لقى {len(data)} شقة - الإجمالي: {len(all_data)}")

        except Exception as e:
            print(f"   ⚠️ مشكلة في الصفحة {page_num}: {e}")
            continue

    driver.quit()

    folder_path = r"D:\Project python 2 sales"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, "properties-details.csv")

    if all_data:
        keys = all_data[0].keys()
        with open(file_path, "w", newline="", encoding="utf-8-sig") as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_data)

        print(f"\n💾 تم الحفظ في: {file_path}")
        print(f"✅ إجمالي الشقق: {len(all_data)}")
    else:
        print("مفيش بيانات اتحفظت")

main()