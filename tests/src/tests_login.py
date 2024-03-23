import pytest
from web_pages import pages, helper
from tests.helper_files import helper as test_helper


@pytest.mark.login_tests
def test_login_page(web_driver):
    login_page = pages.auth.login.LoginPageModel(driver=web_driver)
    login_page.login(username="standard_user", password="secret_sauce")
    
    inventory_page = pages.inventory.inventory.InventoryPage(driver=web_driver, load_page=False).wait_until_loaded()
    assert inventory_page.url in web_driver.current_url, test_helper.get_page_load_error_message(page=inventory_page)