from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import queue
import traceback
import time
import logging
import os
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# Use ChromeDriverManager to handle driver installation
service = Service(ChromeDriverManager().install())

def create_driver(proxy=None):
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    logging.debug(f"Created WebDriver instance with proxy: {proxy}")
    return driver

def send_otp(mobile_number, country, target_website, proxy, results, connected_proxies, failed_proxies):
    driver = None
    try:
        driver = create_driver(proxy)
        if proxy:
            connected_proxies.append(proxy)

        logging.debug(f"Sending OTP to {mobile_number} on {target_website}")

        if target_website == "Spotify":
            driver.get("https://accounts.spotify.com/en-GB/login/phone")
            time.sleep(5)  # Wait for the page to load
            
            # Click to open the dropdown
            country_dropdown = driver.find_element(By.CSS_SELECTOR, "#phonelogin-country")
            country_dropdown.click()
            time.sleep(1)

            # Find and click the option with the country text
            country_option = driver.find_element(By.XPATH, f"//span[contains(text(), '{country}')]")
            country_option.click()
            time.sleep(1)

            # Enter phone number
            phone_input = driver.find_element(By.CSS_SELECTOR, "#phonelogin-phonenumber")
            phone_input.send_keys(mobile_number)
            time.sleep(1)

            # Click the send button
            send_button = driver.find_element(By.CSS_SELECTOR, "#phonelogin-button > span.ButtonInner-sc-14ud5tc-0.liTfRZ.encore-bright-accent-set")
            send_button.click()
            time.sleep(5)  # Wait for the response

            results.append({"number": mobile_number, "status": "success"})

        elif target_website == "TikTok":
            driver.get("https://www.tiktok.com/login/phone-or-email")
            time.sleep(5)  # Wait for the page to load

            # Click and select country code
            country_selector = driver.find_element(By.CSS_SELECTOR, "div.tiktok-1k8r40o-DivAreaLabelContainer.ewblsjs4")
            country_selector.click()
            time.sleep(1)

            # Enter country code
            country_input = driver.find_element(By.CSS_SELECTOR, "#login-phone-search")
            country_input.send_keys(country)
            time.sleep(1)

            # If the country is India, select it from the specific option
            if country.lower() == "india":
                country_option = driver.find_element(By.CSS_SELECTOR, "#IN-91 > span")
                country_option.click()
            else:
                # For other countries, press Enter to select
                country_input.send_keys(Keys.ENTER)
            time.sleep(1)

            # Enter phone number
            phone_input = driver.find_element(By.CSS_SELECTOR, "#loginContainer > div.tiktok-aa97el-DivLoginContainer.exd0a430 > form > div.tiktok-15iauzg-DivContainer.ewblsjs0 > div > div.ewblsjs1.tiktok-bl7zoi-DivInputContainer-StyledBaseInput.etcs7ny0 > input")
            phone_input.send_keys(mobile_number)
            time.sleep(1)

            # Click the submit button
            send_button = driver.find_element(By.CSS_SELECTOR, "#loginContainer > div.tiktok-aa97el-DivLoginContainer.exd0a430 > form > div:nth-child(4) > div > button")
            send_button.click()
            time.sleep(10)  # Wait for the response

            results.append({"number": mobile_number, "status": "success"})

        elif target_website == "Uber":
            driver.get("https://auth.uber.com/v2/")
            time.sleep(5)  # Wait for the page to load

            # Enter mobile number
            phone_input = driver.find_element(By.CSS_SELECTOR, "#PHONE_NUMBER_or_EMAIL_ADDRESS")
            phone_input.send_keys(mobile_number)
            time.sleep(1)

            # Click on the country code dropdown
            country_selector = driver.find_element(By.CSS_SELECTOR, "[data-testid='PHONE_COUNTRY_CODE'] div div span")
            country_selector.click()
            time.sleep(1)

            # Define country-specific selectors
            country_selectors = {
                'afghanistan': "text/🇦🇫Afghanistan+93",
                'albania': "text/🇦🇱Albania+355",
                'algeria': "text/🇩🇿Algeria+213",
                'india': "#bui4val-96",
                'united states': "text/🇺🇸United States+1",
                # Add more countries as needed
            }

            selected_country_selector = country_selectors.get(country.lower())
            if selected_country_selector:
                country_option = driver.find_element(By.XPATH, f"//div[contains(text(), '{selected_country_selector}')]")
                country_option.click()
            else:
                logging.error(f"Country {country} not found in selectors.")
                results.append({"number": mobile_number, "status": "failed", "error": "Country not found in selectors"})
                return
            time.sleep(1)

            # Click the send button
            send_button = driver.find_element(By.CSS_SELECTOR, "#forward-button")
            send_button.click()
            time.sleep(5)  # Wait for the response

            results.append({"number": mobile_number, "status": "success"})

        elif target_website == "Amazon":
            # Navigate to the Amazon sign-in page
            driver.get("https://na.account.amazon.com/ap/signin?_encoding=UTF8&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.pape.max_auth_age=0&ie=UTF8&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=lwa&openid.assoc_handle=amzn_lwa_na&marketPlaceId=ATVPDKIKX0DER&arb=54a00f76-0a69-4182-aa7c-4e3c649f6539&language=en_IN&openid.return_to=https%3A%2F%2Fna.account.amazon.com%2Fap%2Foa%3FmarketPlaceId%3DATVPDKIKX0DER%26arb%3D54a00f76-0a69-4182-aa7c-4e3c649f6539%26language%3Den_IN&enableGlobalAccountCreation=1&metricIdentifier=amzn1.application.eb539eb1b9fb4de2953354ec9ed2e379&signedMetricIdentifier=fLsotU64%2FnKAtrbZ2LjdFmdwR3SEUemHOZ5T2deI500%3D")
            time.sleep(5)  # Wait for the page to load

            # Enter mobile number
            phone_input = driver.find_element(By.CSS_SELECTOR, "#ap_email")
            phone_input.click()
            phone_input.send_keys(mobile_number)
            time.sleep(1)

            # Click the continue button
            continue_button = driver.find_element(By.CSS_SELECTOR, "#continue")
            continue_button.click()
            time.sleep(2)  # Wait for the action to complete

            # Click the continue button again if required
            continue_button = driver.find_element(By.CSS_SELECTOR, "#auth-login-via-otp-btn")
            continue_button.click()
            time.sleep(5)  # Wait for the response

            # Wait for the OTP input field to appear
            try:
                otp_input_field = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#cvf-input-code"))
                )
                driver.save_screenshot('amazon_otp_input_field.png')
                if otp_input_field:
                    results.append({"number": mobile_number, "status": "success"})
                else:
                    results.append({"number": mobile_number, "status": "failure"})
            except TimeoutException:
                results.append({"number": mobile_number, "status": "failure", "error": "OTP field not found"})

    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"Error occurred while sending OTP: {e}")
        results.append({"number": mobile_number, "status": "failure", "error": str(e)})
    finally:
        if driver:
            driver.quit()

@app.route('/send_otp', methods=['POST'])
def send_otp_route():
    data = request.json
    mobile_number = data.get("mobile_number")
    country = data.get("country")
    target_website = data.get("target_website")
    proxy = data.get("proxy", None)

    results = []
    connected_proxies = []
    failed_proxies = []

    # Create a queue for processing requests
    request_queue = queue.Queue()
    request_queue.put((mobile_number, country, target_website, proxy))

    # Define a worker thread to process the queue
    def worker():
        while not request_queue.empty():
            mobile_number, country, target_website, proxy = request_queue.get()
            send_otp(mobile_number, country, target_website, proxy, results, connected_proxies, failed_proxies)
            request_queue.task_done()

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to port 5000 if PORT is not set
    app.run(debug=True, host='0.0.0.0', port=port)
