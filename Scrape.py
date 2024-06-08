from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
import os
from PIL import Image
import pytesseract
import re
import sqlite3
import base64

# Setup Selenium WebDriver for Edge
options = webdriver.EdgeOptions()
options.add_experimental_option("detach", True)
driver = webdriver.Edge(options=options)

# URL of the Google Images search result
url = 'https://www.google.com/search?q=menu+images+of+all+restaurants+in+mumbai&tbm=isch'

driver.get(url)

# Scroll to load more images (optional)
for _ in range(3):
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

# Get page source and parse with BeautifulSoup
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

# Find image URLs
image_tags = soup.find_all('img')
image_urls = [img['src'] for img in image_tags if 'src' in img.attrs]

# Close the WebDriver
driver.quit()

# Download images
download_folder = 'menu_images'
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# Filter out invalid URLs
valid_image_urls = [url for url in image_urls if url.startswith('http')]

# Download images
image_paths = []
for i, img_url in enumerate(valid_image_urls):
    try:
        response = requests.get(img_url)
        img_path = os.path.join(download_folder, f'menu_{i}.jpg')
        with open(img_path, 'wb') as f:
            f.write(response.content)
        image_paths.append(img_path)
    except Exception as e:
        print(f"Could not download image {img_url}: {e}")

print(f'Downloaded images: {image_paths}')

# Specify the path to Tesseract executable if not in PATH
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-installer\tesseract.exe'

# Perform OCR on downloaded images
ocr_results = []
for image_path in image_paths:
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        ocr_results.append(text)
        print(f'OCR Result for {image_path}:\n{text}\n')
    except Exception as e:
        print(f"Could not perform OCR on {image_path}: {e}")

# Parsing OCR Output (extracting menu items and prices)
def parse_ocr_output(text):
    items = []
    lines = text.split('\n')
    for line in lines:
        match = re.match(r'(.+?)\s+(\d+\.?\d*)$', line)
        if match:
            item_name = match.group(1).strip()
            price = float(match.group(2).strip())
            items.append((item_name, price))
    return items

menu_items = []
for text in ocr_results:
    items = parse_ocr_output(text)
    menu_items.extend(items)

print(f'Parsed Menu Items: {menu_items}')

# Storing in SQLite Database
def create_database(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS menu
                      (id INTEGER PRIMARY KEY, item_name TEXT, price REAL)''')
    conn.commit()
    return conn

def insert_menu_items(conn, items):
    cursor = conn.cursor()
    cursor.executemany('INSERT INTO menu (item_name, price) VALUES (?, ?)', items)
    conn.commit()

db_name = 'restaurant_menus.db'
conn = create_database(db_name)
insert_menu_items(conn, menu_items)
conn.close()

print(f'Data successfully stored in {db_name}')


import psycopg2

# Function to create PostgreSQL database connection
def create_database_connection():
    conn = psycopg2.connect(
        dbname="Menu_items",
        user="postgres",
        password="gopalkhan",
        host="localhost",
        port="5432"
    )
    return conn

# Function to insert menu items into the PostgreSQL database
def insert_menu_items_to_postgres(conn, items):
    cursor = conn.cursor()
    for item in items:
        cursor.execute("INSERT INTO menu (item_name, price) VALUES (%s, %s)", (item[0], item[1]))
    conn.commit()

# Connect to the PostgreSQL database
conn = create_database_connection()

# Insert menu items into the PostgreSQL database
insert_menu_items_to_postgres(conn, menu_items)

# Close the database connection
conn.close()

print("Data successfully stored in PostgreSQL database.")