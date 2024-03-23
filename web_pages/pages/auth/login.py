"""Page objects for login page"""
import web_pages
import furl
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import element_to_be_clickable, visibility_of
from six import raise_from

from web_pages.pages.auth import exceptions
from web_pages.core import page_model

__all__ = ["LoginPageModel", "LogInFailedException"]

class LoginPageModel(page_model.PageModel):
    """
    Login page of the application
    """
    url = "/"

    username = page_model.element((By.ID, "user-name"))
    password = page_model.element((By.ID, "password"))
    submit = page_model.element((By.ID, "login-button"))
    error = page_model.element((By.CSS_SELECTOR, ".error-message-container.error"))

    def _is_on_login_page(self):
        """Check if the current url is for the login page (ignoring any redirect/next query)"""
        # We only compare the `path` component
        return self.url == str(furl.furl(self.driver.current_url).path)


    def is_loaded(self):
        return self._is_on_login_page() and element_to_be_clickable((By.CLASS_NAME, "login_credentials_wrap"))(
            self.driver
        )


    def _login(self, username, password):
        self.username.set_text(username)
        self.password.set_text(password)
        self.submit.click()


    def login(self, username, password):
        self._login(username, password)
        try:
            self.wait_for(lambda _: not self._is_on_login_page(), timeout=10)
        except exceptions.TimeoutException as exc:
            raise_from(
                web_pages.pages.auth.exceptions.LogInFailedException(
                    "Login failed with user: {!r} and password: {!r}".format(username, password)
                ),
                exc,
            )
        # Avoid circular dependency
        from web_pages import helper

        # Depending on the user account privileges different pages could be returned
        return helper.lookup_page_for_url(self.driver.current_url)(self.driver)


    def login_with_wrong_credentials(self, username="wrong", password="wrong"):
        self._login(username, password)
        self.wait_until_loaded()

    def login_alert_message(self):
        alert_element = self.wait_for(visibility_of(self.alert))
        return alert_element.text