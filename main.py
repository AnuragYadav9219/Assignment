from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import csv
import json
import os

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "path_to_chromedriver")

    if not os.path.isfile(chromedriver_path):
        raise FileNotFoundError(f"Chromedriver not found at: {chromedriver_path}")

    service = Service(chromedriver_path)
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        raise RuntimeError(f"Failed to initialize the web driver: {e}")
    return driver

def authenticate_amazon(driver, email, password):
    login_url = "https://www.amazon.in/ap/signin"
    driver.get(login_url)

    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        )
        email_field.send_keys(email)
        driver.find_element(By.ID, "continue").click()

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        )
        password_field.send_keys(password)
        driver.find_element(By.ID, "signInSubmit").click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "nav-link-accountList"))
        )
        print("Login successful.")

    except TimeoutException:
        print("Login failed. Check your credentials or network.")
        driver.quit()
        exit()

def scrape_category(driver, category_url):
    driver.get(category_url)
    products = []

    for _ in range(15):
        try:
            product_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.zg-grid-general-faceout"))
            )

            for product in product_elements:
                try:
                    product_name = product.find_element(By.CSS_SELECTOR, "span.zg-text-center-align a.a-link-normal").text
                    product_price = product.find_element(By.CSS_SELECTOR, "span.p13n-sc-price").text if product.find_elements(By.CSS_SELECTOR, "span.p13n-sc-price") else "Not available"
                    discount = "Not available"
                    rating = product.find_element(By.CSS_SELECTOR, "span.a-icon-alt").text if product.find_elements(By.CSS_SELECTOR, "span.a-icon-alt") else "Not available"
                    images = [img.get_attribute('src') for img in product.find_elements(By.CSS_SELECTOR, "img")]

                    products.append({
                        "Product Name": product_name,
                        "Product Price": product_price,
                        "Sale Discount": discount,
                        "Best Seller Rating": rating,
                        "Images": images
                    })
                except NoSuchElementException:
                    continue

            next_buttons = driver.find_elements(By.CSS_SELECTOR, "li.a-last a")
            if next_buttons:
                next_button = next_buttons[0]
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)
            else:
                break

        except TimeoutException:
            break

    return products

def save_data(data, file_format='csv', filename='amazon_data'):
    if data:
        if file_format == 'csv':
            with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        elif file_format == 'json':
            with open(f"{filename}.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
    else:
        print("No data to save.")

def main():
    driver = None
    try:
        driver = setup_driver()
        email = os.getenv("AMAZON_EMAIL", "your_email@example.com")
        password = os.getenv("AMAZON_PASSWORD", "your_password")

        authenticate_amazon(driver, email, password)

        category_urls = [
            "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
            "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
            "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
            "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0"
        ]

        all_products = []

        for category_url in category_urls:
            print(f"Scraping category: {category_url}")
            category_products = scrape_category(driver, category_url)
            all_products.extend(category_products)

        save_data(all_products, file_format='csv', filename='amazon_best_sellers')

    except FileNotFoundError as e:
        print(e)
    except RuntimeError as e:
        print(e)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
