import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def create_driver(proxy=None):
    options = Options()
    options.add_argument('--headless')  # Run headlessly if desired
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
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

            try:
                country_selector = driver.find_element(By.CSS_SELECTOR, "div.tiktok-1k8r40o-DivAreaLabelContainer.ewblsjs4")
                country_selector.click()
                time.sleep(1)

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

                driver.save_screenshot('tiktok_screenshot.png')
                logs = driver.get_log('browser')
                for log in logs:
                    logging.error(log)

                results.append({"number": mobile_number, "status": "success"})
            except NoSuchElementException as e:
                logging.error(f"Element not found during TikTok OTP process: {str(e)}")
                results.append({"number": mobile_number, "status": "failure", "error": f"Element not found: {str(e)}"})
            except TimeoutException as e:
                logging.error(f"Timeout during TikTok OTP process: {str(e)}")
                results.append({"number": mobile_number, "status": "failure", "error": f"Timeout: {str(e)}"})
            except Exception as e:
                logging.error(f"Error during TikTok OTP process: {str(e)}")
                results.append({"number": mobile_number, "status": "failure", "error": str(e)})

        elif target_website == "Amazon":
            driver.get("https://na.account.amazon.com/ap/signin?_encoding=UTF8...")
            time.sleep(5)  # Wait for the page to load

            try:
                phone_input = driver.find_element(By.CSS_SELECTOR, "#ap_email")
                phone_input.click()
                phone_input.send_keys(mobile_number)
                time.sleep(1)

                continue_button = driver.find_element(By.CSS_SELECTOR, "#continue")
                continue_button.click()
                time.sleep(2)

                continue_button = driver.find_element(By.CSS_SELECTOR, "#auth-login-via-otp-btn")
                continue_button.click()
                time.sleep(5)

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
            except NoSuchElementException as e:
                logging.error(f"Element not found during Amazon OTP process: {str(e)}")
                results.append({"number": mobile_number, "status": "failure", "error": f"Element not found: {str(e)}"})
            except WebDriverException as e:
                logging.error(f"WebDriver exception during Amazon OTP process: {str(e)}")
                results.append({"number": mobile_number, "status": "failure", "error": f"WebDriver exception: {str(e)}"})
            except Exception as e:
                logging.error(f"Error during Amazon OTP process: {str(e)}")
                results.append({"number": mobile_number, "status": "failure", "error": str(e)})

    except Exception as e:
        logging.error(f"Unexpected error for {mobile_number}: {str(e)}")
        results.append({"number": mobile_number, "status": "failed", "error": str(e)})
        if proxy:
            failed_proxies.append(proxy)
    finally:
        if driver:
            driver.quit()
            logging.debug(f"WebDriver instance closed for {mobile_number}")
