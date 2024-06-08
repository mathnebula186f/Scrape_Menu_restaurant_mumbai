import json
import requests
import os
from PIL import Image
import pytesseract
import psycopg2
import re
import hashlib


# Specify the path to Tesseract executable if not in PATH
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-installer\tesseract.exe'


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


# Function to create a table for each image URL
def create_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                      (id SERIAL PRIMARY KEY, item_name TEXT, price REAL)''')
    conn.commit()


# Function to insert menu items into the PostgreSQL database for a specific table
def insert_menu_items_to_postgres(conn, table_name, items):
    if items is not None:
        cursor = conn.cursor()
        cursor.executemany(f'INSERT INTO {table_name} (item_name, price) VALUES (%s, %s)', items)
        conn.commit()
    else:
        print(f"No menu items found for table '{table_name}'. Skipping insertion.")


# Function to delete all records from all tables in the database
def delete_all_records(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public';")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DELETE FROM {table[0]};")
    conn.commit()


# Read JSON file containing menu image URLs
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['menu_images']


# Function to delete all images from the menu_images folder
def delete_all_images(image_folder):
    try:
        file_list = os.listdir(image_folder)
        for file_name in file_list:
            file_path = os.path.join(image_folder, file_name)
            os.remove(file_path)
        print("All images deleted from 'menu_images' folder.")
    except Exception as e:
        print(f"Error deleting images: {e}")


# Function to download and save image
def download_image(image_url, image_folder):
    try:
        # Get image name from URL
        image_name = image_url.split('/')[-1]
        image_path = os.path.join(image_folder, image_name)

        # Download image
        response = requests.get(image_url)
        with open(image_path, 'wb') as f:
            f.write(response.content)

        return image_path
    except Exception as e:
        print(f"Could not download image from {image_url}: {e}")
        return None


# Function to perform OCR on the images
def perform_ocr(menu_images):
    menu_items = {}
    for index, image_url in enumerate(menu_images):
        try:
            # Download image
            image_path = download_image(image_url, 'menu_images')
            if image_path:
                # Perform OCR on the downloaded image
                text = pytesseract.image_to_string(Image.open(image_path))
                # print(text)

                # Extract menu items and prices
                items = parse_ocr_output(text)
                menu_items[image_url] = items
                # print(items)
        except Exception as e:
            print(f"Could not process image at index {index}: {e}")

    return menu_items


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


# Generate a valid table name from the image URL
def generate_table_name(image_url):
    # Use a hashing algorithm to generate a unique table name
    hash_object = hashlib.md5(image_url.encode())
    return 'menu_' + hash_object.hexdigest()


# Main function
def main():
    # Read JSON file
    json_file_path = 'menu_images.json'
    menu_images = read_json_file(json_file_path)

    # Connect to the PostgreSQL database
    conn = create_database_connection()

    # Delete all records from all tables in the database
    delete_all_records(conn)

    # Delete all images from the menu_images folder
    delete_all_images('menu_images')

    # Perform OCR on menu images
    menu_items = perform_ocr(menu_images)

    # Process each image's menu items
    for image_url, items in menu_items.items():
        # Generate a table name for the image URL
        table_name = generate_table_name(image_url)

        # Create a table for the image URL if it doesn't exist
        create_table(conn, table_name)

        # Insert menu items into the PostgreSQL database for the corresponding table
        insert_menu_items_to_postgres(conn, table_name, items)

    # Close the database connection
    conn.close()

    print("Data successfully stored in PostgreSQL database.")


if __name__ == "__main__":
    main()
