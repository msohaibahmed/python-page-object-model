"""Helper methods for test automation."""
import random
from urllib.parse import urlparse

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


def is_element_clickable(element_to_be_checked):
    """Check if element is clickable."""
    return element_to_be_checked.is_enabled() and element_to_be_checked.is_displayed()

def get_random_item_from_list(input_list, exclude_values=None):
    """Get random value from list."""
    if exclude_values is not None:
        return random.choice([item for item in input_list if item != exclude_values])
    return random.choice(input_list)


def is_radio_btn_has_valid_value(radio_button_element, valid_value):
    """Check if radio button has valid value."""
    selected_value = ""
    if radio_button_element.is_selected():
        selected_value = radio_button_element.get_attribute("value")
    return valid_value == selected_value


def is_element_clickable_and_has_value(element_to_be_checked, value):
    """Check if element is enabled and has expected value."""
    return (
        is_element_clickable(element_to_be_checked=element_to_be_checked)
        and element_to_be_checked.text == value
    )


def has_dropdown_expected_options(dropdown_element, expected_values):
    """Check if dropdown has expected options."""
    actual_values = dropdown_element.options_values
    return sorted(actual_values) == sorted(expected_values)

def is_value_selection_in_dropdown_successful(dropdown_element, value_to_verify):
    """Check if value selection in dropdown is successful."""
    dropdown_element.select_by_value(value_to_verify)
    selected_value = dropdown_element.selected_value
    return value_to_verify == selected_value

def is_text_field_editable_and_has_expected_value(text_field, expected_value):
    """Check if text field is enabled and has expected value."""
    return is_element_clickable(text_field) and text_field.get_text() == expected_value

def is_string_in_web_element_list(web_element_list, target_string):
    """Check if the target string is present in the text of any WebElement in the list."""
    for element in web_element_list:
        # Ensure the element is a WebElement
        if isinstance(element, WebElement):
            if target_string in element.text:
                return True
    return False


def wait_until_dialog_box_is_closed(web_driver, dialog_box):
    """Wait until dialog box is closed."""
    WebDriverWait(web_driver, 10).until(
        expected_conditions.invisibility_of_element_located(dialog_box)
    )


def get_page_load_error_message(page):
    """Method to return error statement based on web_page."""
    return f"Error: Loading '{type(page).__name__}' page with url '{page.url}'."


def wait_until_element_is_visible(web_driver, web_element):
    """Wait until web element is visible on page."""
    WebDriverWait(web_driver, 10).until(
        expected_conditions.presence_of_element_located(web_element)
    )


def open_menu_list(web_driver, menu_item):
    """Method to open menu items to access sub-menu."""
    action = ActionChains(web_driver)
    action.move_to_element(menu_item).perform()


def extract_path_from_url(url):
    """Get url without base url."""
    parsed_url = urlparse(url)
    return parsed_url.path