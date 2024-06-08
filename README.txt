ASSIGNMENT SUBMISSION FOR REBALANCE TECHNOLOGIES

Method (1) Using Scrape_Image.py

-In here i have made a menu_images.json file Which contains URLs of images of various restaurants of Mumbai
-Im Using Tesseract performing OCR on all those images after scraping them locally
- im reading the items and prices
-Im Storing them in my PGAdmin Database (columns for items and prices have been made)


Method (2) Using Scrape.py

-This performs similar thing but just scrapes images from google search of Menus of restaurants of mumbai
-This method (2) is not preffered because-
a) Images being scrapped by beautiful soup (using img src of selenium) are  small and Tesseract cannot preform ocr on
b) Some misc images are also being scraped which aren't useful and filling database wastefully


Just run  python Scrape_Image.py for running method (1) and python Scrape.py for running method (2)

Thanks!! Nice ASSIGNMENT By you though



