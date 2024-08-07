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

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--headless")
chrome_options.add_argument("window-size=1200x600")
chrome_options.add_argument("user-agent=Your User Agent String")
chrome_options.binary_location = os.getenv('CHROME_BINARY_LOCATION', '/opt/render/project/.render/chrome/opt/google/chrome/chrome')

# Thread-safe queue for OTP requests
otp_queue = queue.Queue()

def create_driver(proxy=None):
    service = Service(os.getenv('CHROMEDRIVER_PATH', '/opt/render/project/.render/chromedriver/chromedriver'))
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

        if target_website == "TikTok":
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

            if country.lower() == "india":
                country_option = driver.find_element(By.CSS_SELECTOR, "#IN-91 > span")
                country_option.click()
            else:
                country_input.send_keys(Keys.ENTER)
            time.sleep(1)

            phone_input = driver.find_element(By.CSS_SELECTOR, "#loginContainer > div.tiktok-aa97el-DivLoginContainer.exd0a430 > form > div.tiktok-15iauzg-DivContainer.ewblsjs0 > div > div.ewblsjs1.tiktok-bl7zoi-DivInputContainer-StyledBaseInput.etcs7ny0 > input")
            phone_input.send_keys(mobile_number)
            time.sleep(1)

            send_button = driver.find_element(By.CSS_SELECTOR, "#loginContainer > div.tiktok-aa97el-DivLoginContainer.exd0a430 > form > div:nth-child(4) > div > button")
            send_button.click()
            time.sleep(10)  # Wait for the response

            # Debugging
            driver.save_screenshot('tiktok_screenshot.png')
            logs = driver.get_log('browser')
            for log in logs:
                logging.error(log)

            results.append({"number": mobile_number, "status": "success"})

        elif target_website == "Amazon":
            driver.get("https://na.account.amazon.com/ap/signin?_encoding=UTF8&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.pape.max_auth_age=0&ie=UTF8&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=lwa&openid.assoc_handle=amzn_lwa_na&marketPlaceId=ATVPDKIKX0DER&arb=54a00f76-0a69-4182-aa7c-4e3c649f6539&language=en_IN&openid.return_to=https%3A%2F%2Fna.account.amazon.com%2Fap%2Foa%3FmarketPlaceId%3DATVPDKIKX0DER%26arb%3D54a00f76-0a69-4182-aa7c-4e3c649f6539%26language%3Den_IN&enableGlobalAccountCreation=1&metricIdentifier=amzn1.application.eb539eb1b9fb4de2953354ec9ed2e379&signedMetricIdentifier=fLsotU64%2FnKAtrbZ2LjdFmdwR3SEUemHOZ5T2deI500%3D")
            time.sleep(5)  # Wait for the page to load

            phone_input = driver.find_element(By.CSS_SELECTOR, "#ap_email")
            phone_input.click()
            phone_input.send_keys(mobile_number)
            time.sleep(1)

            continue_button = driver.find_element(By.CSS_SELECTOR, "#continue")
            continue_button.click()
            time.sleep(2)  # Wait for the action to complete

            continue_button = driver.find_element(By.CSS_SELECTOR, "#auth-login-via-otp-btn")
            continue_button.click()
            time.sleep(5)  # Wait for the response

            # Wait for the OTP input field to appear
            try:
                otp_input_field = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#cvf-input-code"))
                )
                driver.save_screenshot('amazon_otp_input_field.png')
                logs = driver.get_log('browser')
                for log in logs:
                    logging.error(log)
                if otp_input_field:
                    results.append({"number": mobile_number, "status": "success"})
                else:
                    results.append({"number": mobile_number, "status": "failure"})
            except TimeoutException:
                results.append({"number": mobile_number, "status": "failure", "error": "OTP field not found"})

    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"Error sending OTP to {mobile_number}: {str(e)}")
        results.append({"number": mobile_number, "status": "failed", "error": str(e)})
        if proxy:
            failed_proxies.append(proxy)
    except Exception as e:
        logging.error(f"Unexpected error for {mobile_number}: {str(e)}")
        results.append({"number": mobile_number, "status": "failed", "error": str(e)})
        if proxy:
            failed_proxies.append(proxy)
        print(traceback.format_exc())
    finally:
        if driver:
            driver.quit()
            logging.debug(f"WebDriver instance closed for {mobile_number}")

def worker_thread():
    while True:
        mobile_number, country, target_website, proxy, results, connected_proxies, failed_proxies = otp_queue.get()
        send_otp(mobile_number, country, target_website, proxy, results, connected_proxies, failed_proxies)
        otp_queue.task_done()

# Start worker threads
num_worker_threads = 10  # Adjust based on your server capacity
for _ in range(num_worker_threads):
    threading.Thread(target=worker_thread, daemon=True).start()

@app.route('/send-otp', methods=['POST'])
def send_otp_route():
    data = request.json
    mobile_numbers = data.get('mobile_numbers')
    country = data.get('country')
    target_website = data.get('target_website')
    proxies = data.get('proxies')

    results = []
    connected_proxies = []
    failed_proxies = []

    for number in mobile_numbers:
        proxy = proxies[len(results) // 20 % len(proxies)] if proxies else None
        otp_queue.put((number, country, target_website, proxy, results, connected_proxies, failed_proxies))

    otp_queue.join()  # Wait until all tasks are done

    total_sent = len(mobile_numbers)
    success_count = sum(1 for result in results if result['status'] == 'success')
    fail_count = sum(1 for result in results if result['status'] == 'failed')

    logging.debug("All OTP requests processed.")
    return jsonify({
        "results": results,
        "total_sent": total_sent,
        "success_count": success_count,
        "fail_count": fail_count,
        "connected_proxies": list(set(connected_proxies)),
        "failed_proxies": list(set(failed_proxies))
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
