"""Confttest class for fixtures."""
import os
import shutil

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def get_chromedriver_path():
    try:
        chromedriver_path = shutil.which("chromedriver")
        if chromedriver_path:
            return chromedriver_path
        else:
            print("ChromeDriver not found in PATH.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


@pytest.fixture(scope="session")
def web_driver():
    """Returns a Selenium WebDriver instance for the Chrome browser."""
    chrome_driver_path = get_chromedriver_path()
    service = Service(executable_path=chrome_driver_path)
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # driver = webdriver.Chrome(service=service, options=chrome_options)
    driver = webdriver.Chrome()
    yield driver
    driver.quit()