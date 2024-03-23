"""Helper functions to provide certain general interactions with page objects."""
import os
import random
import re
import string
import subprocess
import sys
from datetime import datetime
from enum import Enum


import furl
import six
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from web_pages import pages

# List of all supported page models that can be directly looked up
PAGE_MODELS = [
    #pages.config.account.AccountPage,
]

URL_MAP = {page.url: page for page in PAGE_MODELS}


def lookup_page_for_url(url):
    """Retrieve a page model for a given URL."""
    # So far we only care about the `path` component of the url
    url_path = str(furl.furl(url).path)
    return URL_MAP[url_path]


class DefaultAdmin(object):
    username = "admin"
    password = "admin"

class MessageLevel(Enum):
    def __str__(self):
        return str(self.value)

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class UserCreationWithPasswordFailed(RuntimeError):
    """Exception for failure during user creation with given password."""

    pass

def generate_password():
    valid_characters = (
        string.digits + string.ascii_lowercase + string.ascii_uppercase + string.punctuation
    )
    pwd_chars = [random.choice(valid_characters) for _ in range(11)]
    pwd_chars.append(random.choice(string.digits))
    pwd_chars.append(random.choice(string.ascii_lowercase))
    pwd_chars.append(random.choice(string.ascii_uppercase))
    pwd_chars.append(random.choice(string.punctuation))
    random.shuffle(pwd_chars)
    return "".join(pwd_chars)


def random_ascii_string(n=10):
    """
    Generate a random ASCII string.

    :param n: Number of characters
    :type n: int
    :return: String of length 'n' with lower, upper and digits ASCII characters
    :rtype: string
    """
    return u"".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def find_element_by_regex(driver, regex_expression):
    """find all elements on web page using regular expression."""
    regex_pattern = re.compile(regex_expression)
    elements = WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_all_elements_located((By.XPATH, "//*"))
    )
    return [element for element in elements if regex_pattern.match(element.text)]


def find_paragraphs_with_text(driver, target_text):
    """Get all <p> elements with target text value."""
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.TAG_NAME, "body"))
    )
    paragraphs = driver.find_elements(By.TAG_NAME, "p")
    target_paragraphs = []
    for paragraph in paragraphs:
        if target_text in paragraph.text:
            target_paragraphs.append(paragraph)

    return target_paragraphs


def is_date_time_string(text, date_time_format):
    """Checks if a string represents a date, day, or time in short format."""
    try:
        # Attempt to parse the string as a datetime object using a specific format string
        datetime.strptime(text, date_time_format)
        return True
    except ValueError:
        return False