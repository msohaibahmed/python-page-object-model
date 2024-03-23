import pytest
from web_pages import pages, helper
import time


@pytest.mark.asdfg
def test_login_page(web_driver):
    login_page = pages.auth.login.LoginPageModel(driver=web_driver)
    login_page.username.set_text("username")
    time.sleep(10)
    print(f"current_url: {web_driver.current_url}")
    assert False