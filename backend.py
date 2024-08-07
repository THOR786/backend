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

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.binary_location = "/opt/render/project/.render/chrome/opt/google/chrome/chrome"
# Uncomment the line below to run headlessly (without a UI)
#chrome_options.add_argument("--headless")
# Thread-safe queue for OTP requests
otp_queue = queue.Queue()

def create_driver(proxy=None):
    service = Service("/opt/render/project/.render/chromedriver/chromedriver") # Update with your chromedriver path
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
            
            print('Clicking on the country dropdown')
            # Click to open the dropdown
            country_dropdown = driver.find_element(By.CSS_SELECTOR, "#phonelogin-country")
            country_dropdown.click()
            time.sleep(1)

            print(f'Selecting country: {country}')
            # Find and click the option with the country text
            country_option = driver.find_element(By.XPATH, f"//span[contains(text(), '{country}')]")
            country_option.click()
            time.sleep(1)

            print('Typing the phone number')
            # Enter phone number
            phone_input = driver.find_element(By.CSS_SELECTOR, "#phonelogin-phonenumber")
            phone_input.send_keys(mobile_number)
            time.sleep(1)

            print('Clicking the send button')
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
                'argentina': 'text/Argentina',
                'armenia': 'text/🇦🇲Armenia (Հայաստան)+374',
                'australia': 'text/Australia',
                'azerbaijan': 'text/Azerbaijan (Azərbaycan)',
                'bahamas': 'text/Bahamas',
                'bahrain': 'text/Bahrain (‫البحرين‬‎)',
                'bangladesh': 'text/Bangladesh (বাংলাদেশ)',
                'belarus': 'text/🇧🇾Belarus (Беларусь)+375',
                'belgium': 'text/Belgium (België)',
                'brazil': 'text/Brazil (Brasil)',
                'canada': 'text/Canada',
                'colombia': 'text/Colombia',
                'denmark': 'text/Denmark (Danmark)',
                'egypt': 'text/Egypt (‫مصر‬‎)',
                'ethiopia': 'text/🇪🇹Ethiopia+251',
                'france': 'text/🇫🇷France+33',
                'germany': 'text/Germany (Deutschland)',
                'greece': 'text/🇬🇷Greece (Ελλάδα)+30',
                'hong kong': 'text/Hong Kong (香港)',
                'hungary': 'text/Hungary (Magyarország)',
                'indonesia': 'text/🇮🇩Indonesia+62',
                'iran': 'text/🇮🇷Iran (‫ایران‬‎)+98',
                'iraq': 'text/🇮🇶Iraq (‫العراق‬‎)+964',
                'israel': 'text/Israel (‫ישראל‬‎)',
                'japan': 'text/Japan (日本)',
                'lebanon': 'text/Lebanon (‫لبنان‬‎)',
                'luxembourg': 'text/Luxembourg',
                'malaysia': 'text/🇲🇾Malaysia+60',
                'maldives': 'text/Maldives',
                'mexico': 'text/Mexico (México)',
                'morocco': 'text/Morocco (‫المغرب‬‎)',
                'new zealand': 'text/New Zealand',
                'north korea': 'text/North Korea (조선)',
                'oman': 'text/Oman (‫عُمان‬‎)',
                'pakistan': 'text/Pakistan (‫پاکستان‬‎)',
                'palestine': 'text/Palestine (‫فلسطين‬‎)',
                'portugal': 'text/🇵🇹Portugal+351',
                'qatar': 'text/Qatar (‫قطر‬‎)',
                'russia': 'text/Russia (Россия)',
                'saudi arabia': 'text/Saudi Arabia',
                'singapore': 'text/🇸🇬Singapore+65',
                'south africa': 'text/South Africa',
                'south korea': 'text/South Korea (대한민국)',
                'sri lanka': 'text/Sri Lanka (ශ්‍රී)',
                'switzerland': 'text/Switzerland (Schweiz)',
                'syria': 'text/Syria (‫سوريا‬‎)',
                'taiwan': 'text/🇹🇼Taiwan (台灣)+886',
                'turkey': 'text/Turkey (Türkiye)',
                'ukraine': 'text/Ukraine (Україна)',
                'united arab': 'text/🇦🇪United Arab',
                'united kingdom': 'text/🇬🇧United Kingdom+44',
                'yemen': 'text/Yemen (‫اليمن‬‎)'
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
            continue_button = driver.find_element(By.CSS_SELECTOR, "#continue")
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


