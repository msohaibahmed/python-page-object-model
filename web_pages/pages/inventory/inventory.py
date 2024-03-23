"""Page object model for inventory page."""

from selenium.webdriver.common import by
from selenium.webdriver.support import expected_conditions

from web_pages import shared
from web_pages.core import page_model

class InventoryPage(shared.StandardPageModel):

    url = "/inventory.html"

    def is_loaded(self):
        return super(
            InventoryPage, self
        ).is_loaded() and expected_conditions.visibility_of_element_located(
            (by.By.ID, "page_wrapper")
        )(
            self.driver
        )
