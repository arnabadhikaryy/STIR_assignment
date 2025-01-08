from flask import Flask, render_template, redirect, url_for
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

app = Flask(__name__)

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")  # MongoDB URI
db = client["twitter_trends"]  # Database name
collection = db["trending_news"]  # Collection name

# Route to display the webpage with the 'Find Trends' button
@app.route('/')
def index():
    return render_template('index.html')

# Route to trigger scraping and store data in MongoDB
@app.route('/find_trends')
def find_trends():
    # Selenium Setup
    driver = webdriver.Chrome()
    driver.get("https://x.com/?lang=en-in")

    wait = WebDriverWait(driver, 10)

    # Login Process
    i_have_account_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Sign in']")))
    i_have_account_button.click()

    email_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='text']")))
    email_input.send_keys("adhikaryarnab977@gmail.com")
    time.sleep(5)

    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Next']")))
    next_button.click()
    time.sleep(5)

    # Handle optional username step
    try:
        username_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='text']")))
        username_input.send_keys("HaranKu11459620")
        time.sleep(2)

        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Next']")))
        next_button.click()
        time.sleep(2)
    except Exception as e:
        print("Username step skipped, proceeding to password.")

    # Wait for password input
    password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='password']")))
    password_input.send_keys("55555@Arnab")

    # Log in
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Log in']")))
    login_button.click()
    time.sleep(5)

    # Navigate to Trending Section
    show_more_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Show more']")))
    show_more_button.click()
    time.sleep(5)

    trending_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Trending']")))
    trending_button.click()
    time.sleep(5)

    # Scrape Trending Hashtags
    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//span[contains(@class, 'css-1jxf684')]")))
    time.sleep(3)  # Additional wait for complete loading

    trending_hashtags = driver.find_elements(By.XPATH, "//span[contains(@class, 'css-1jxf684') and text()[starts-with(., '#')]]")

    # Debug: Print the number of hashtags found
    print(f"Found {len(trending_hashtags)} trending hashtags.")

    # Extract the first 5 trending hashtags if available
    if len(trending_hashtags) >= 5:
        trending_object = {f"trending_{i + 1}": trending_hashtags[i].text for i in range(5)}
    else:
        # Handle fewer than 5 hashtags gracefully
        trending_object = {f"trending_{i + 1}": trending_hashtags[i].text for i in range(len(trending_hashtags))}

    # Add current timestamp
    trending_object["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update MongoDB
    collection.update_one(
        {"_id": "trending_news_id"},  # Static ID for simplicity
        {"$push": {"trending_news": trending_object}},  # Push new object into the array
        upsert=True  # Create document if it doesn't exist
    )

    print("Data inserted into MongoDB:", trending_object)

    # Close the browser
    driver.close()

    # Close MongoDB connection
   # client.close()

    return redirect(url_for('view_data'))

# Route to view the scraped data from MongoDB
@app.route('/view_data')
def view_data():
    data = collection.find_one({"_id": "trending_news_id"})
    if data and "trending_news" in data:
        trends = data["trending_news"]
    else:
        trends = []

    return render_template('view_data.html', trends=trends)

if __name__ == '__main__':
    app.run(debug=True)
