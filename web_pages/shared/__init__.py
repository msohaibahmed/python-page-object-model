"""Collection of shared parts of pages and a standard page layout."""
from abc import ABCMeta


from selenium.webdriver.common.by import By
from core import page_model

__all__ = ["StandardPageModel"]

class StandardPageModel(
    page_model.PageModel
):  # pylint:disable=abstract-method; Abstract Subclass, not concrete
    """
    Base class for any standard page application.

    This provides the navigation fragment bar
    """


    __metaclass__ = ABCMeta
    #navigation_bar = page_model.fragment(navigation_bar.NavigationBar)


    def find_flash_messages(self, driver=None, message_level=None):
        """Get all flash messages elements from page."""
        if not message_level:
            selector_name = ".alert-box"
        else:
            selector_name = ".alert-box.{}".format(message_level)
        return driver.find_elements(By.CSS_SELECTOR, selector_name)