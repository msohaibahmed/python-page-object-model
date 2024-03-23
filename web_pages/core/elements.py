"""
Page elements for page object models

This module contains extension classes that represent different
elements on web pages represented by a page object model.

These classes offer better support for interacting with common elements like select
fields, text inputs or the chosen select containers we are using in our application.

They have a selector method that determines whether they match a given page element. The actual
lookup is handled by a factory class that provides the first registered matching extension.
The factory again is associated with a page object model. This design allows for an individual
page to create a different factory class and register page specific extensions it needs to.
"""
import sys
from inspect import cleandoc

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import (
    visibility_of,
    visibility_of_element_located,
)
from selenium.webdriver.support.ui import Select, WebDriverWait

_all_ = [
    "ExtendedWebElement",
    "CheckboxInput",
    "TextInput",
    "TextArea",
    "NumberInput",
    "PasswordInput",
    "RadioButton",
    "SingleSelect",
    "MultiSelect",
    "SingleChosenSelect",
    "MultiChosenSelect",
    "WebElementExtension",
    "DEFAULT_EXTENSIONS",
]

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


class ExtendedWebElement(WebElement):
    """Extend the WebElement with functionality"""

    def __init__(self, parent, id, extension_factory, timeout, **kwargs):
        super(ExtendedWebElement, self).__init__(parent, id, **kwargs)
        self._extension_factory = extension_factory
        self.timeout = timeout
        if not self.selector(self):
            raise ValueError("Invalid element used for {}".format(self._class.name_))

    @classmethod
    def from_web_element(cls, web_element, extension_factory, timeout, **kwargs):
        if PY2:
            web_element = cls(
                parent=web_element._parent,  # pylint:disable=protected-access
                id=web_element._id,  # pylint:disable=protected-access
                extension_factory=extension_factory,
                timeout=timeout,
                w3c=web_element._w3c,  # pylint:disable=protected-access
                **kwargs
            )
        else:
            web_element = cls(
                parent=web_element._parent,  # pylint:disable=protected-access
                id=web_element._id,  # pylint:disable=protected-access
                extension_factory=extension_factory,
                timeout=timeout,
                **kwargs
            )
        return web_element

    def _create_element_from_factory(self, web_element, **kwargs):
        """Return a new extension element object from the factory class"""
        return self._extension_factory(web_element=web_element, timeout=self.timeout, **kwargs)

    @staticmethod
    def selector(element):  # pylint:disable=unused-argument
        """Overwrite this method in child-classes to provide the lookup function"""
        return True

    def wait_for(self, wait_fcn, message="", **kwargs):
        def drop_driver_wrapper(_driver):
            return wait_fcn()

        return WebDriverWait(self.parent, self.timeout, **kwargs).until(
            drop_driver_wrapper, message=message
        )

    def wait_until_clickable(self):
        return self.wait_for(self.element_is_clickable)

    def element_is_clickable(self):
        """Check if element is clickable"""
        # PY3: With Python3 and Selenium>=4.0 this is properly covered by
        # element_to_be_clickable from the expected_conditions module.
        target = visibility_of(self)(self)
        return bool(target and target.is_enabled())

    def following_sibling(self):
        return self._create_element_from_factory(
            web_element=self.find_element(By.XPATH, "./following-sibling::*")
        )

    def preceding_sibling(self):
        return self._create_element_from_factory(
            web_element=self.find_element(By.XPATH, "./preceding-sibling::*")
        )

    def find_field_error(self):
        return self._create_element_from_factory(
            web_element=self.find_element(
                By.CSS_SELECTOR, '.form-field-error, p[style*="color: red"]'
            )
        )


class CheckboxInput(ExtendedWebElement):
    """A <input type='checkbox'> element"""

    @staticmethod
    def selector(element):
        return element.tag_name == "input" and element.get_attribute("type") == "checkbox"

    def select(self):
        if not self.is_selected():
            self.click()
            self.wait_for(self.is_selected)

    def deselect(self):
        if self.is_selected():
            self.click()
            self.wait_for(lambda: not self.is_selected())

    def set_select_status(self, status):
        if status:
            self.select()
        else:
            self.deselect()


class TextInput(ExtendedWebElement):
    """A <input type='text'> element"""

    @staticmethod
    def selector(element):
        return element.tag_name == "input" and element.get_attribute("type") == "text"

    def get_text(self):
        return self.get_attribute("value")

    def set_text(self, value):
        self.wait_until_clickable()
        self.clear_text()
        self.send_keys(value)
        self.wait_for(lambda: self.get_text() == value)

    def clear_text(self):
        self.clear()
        self.wait_for(lambda: self.get_text() == "")


class TextArea(ExtendedWebElement):
    """A <input type='text'> element"""

    @staticmethod
    def selector(element):
        return element.tag_name == "textarea"

    def get_text(self):
        return self.get_attribute("value")

    def set_text(self, value):
        self.wait_until_clickable()
        self.clear_text()
        self.send_keys(value)
        self.wait_for(lambda: self.get_text() == value)

    def clear_text(self):
        self.clear()
        self.wait_for(lambda: self.get_text() == "")


class NumberInput(TextInput):
    """A <input type='number'> element."""

    @staticmethod
    def selector(element):
        return element.tag_name == "input" and element.get_attribute("type") == "number"


class PasswordInput(TextInput):
    """A <input type='password'> element"""

    @staticmethod
    def selector(element):
        return element.tag_name == "input" and element.get_attribute("type") == "password"


class RadioButton(ExtendedWebElement):
    """A <input type='radio'> element"""

    @staticmethod
    def selector(element):
        return element.tag_name == "input" and element.get_attribute("type") == "radio"

    def select(self):
        self.click()
        self.wait_for(self.is_selected)


class _SelectInput(ExtendedWebElement):
    """
    Base class for <select> elements

    Provides direct access to all helper functions from Selenium Select Support, see
    :py:class:selenium.webdriver.support.select.Select for available methods and properties.
    """

    def __init__(self, *args, **kwargs):
        super(_SelectInput, self).init_(*args, **kwargs)
        self.select = Select(self)

    def _getattr_(self, item):
        if hasattr(self.select, item):
            return getattr(self.select, item)
        raise AttributeError("type object 'SelectInput' has no attribute '{}'".format(item))

    @property
    def options_values(self):
        return [option.get_attribute("value") for option in self.options]

    @property
    def options_texts(self):
        return [option.text for option in self.options]


class SingleSelect(_SelectInput):
    """
    A <select> element that can select a single value (without "multiple" attribute)

    Provides direct access to all helper functions from Selenium Select Support, see
    :py:class:selenium.webdriver.support.select.Select for available methods and properties.
    """

    @staticmethod
    def selector(element):
        return element.tag_name == "select" and element.get_attribute("multiple") is None

    @property
    def selected_option(self):
        return self.select.first_selected_option

    @property
    def selected_value(self):
        return self.selected_option.get_attribute("value")

    @property
    def selected_text(self):
        return self.selected_option.get_attribute("text")


class MultiSelect(_SelectInput):
    """
    A <select multiple=""> element

    Provides direct access to all helper functions from Selenium Select Support, see
    :py:class:selenium.webdriver.support.select.Select for available methods and properties.
    """

    @staticmethod
    def selector(element):
        return element.tag_name == "select" and element.get_attribute("multiple") is not None

    @property
    def selected_values(self):
        return [x.get_attribute("value") for x in self.select.all_selected_options]

    @property
    def selected_texts(self):
        return [x.get_attribute("text") for x in self.select.all_selected_options]


class _ChosenContainer(ExtendedWebElement):
    """
    A <div class="chosen-container"> for a <select class="chosen-select> element

    Helper class to deal with the Chosen JQuery plugin select containers.
    """

    def _init(self, parent, id_, extension_factory, timeout, **kwargs):
        super(_ChosenContainer, self).init_(
            parent=parent, id_=id_, extension_factory=extension_factory, timeout=timeout, **kwargs
        )
        parent_select = self.find_element(By.XPATH, "./preceding-sibling::select")
        self._select = self._create_element_from_factory(parent_select)
        self.select = Select(parent_select)
        try:
            self.search_field = self._create_element_from_factory(
                self.find_element(By.CLASS_NAME, "chosen-search-input")
            )
        except NoSuchElementException:
            self.search_field = None

    def drop_down_visible(self):
        return visibility_of_element_located((By.CLASS_NAME, "chosen-drop"))(self)

    def open_drop_down(self):
        self.parent.execute_script("$(arguments[0]).trigger('chosen:open')", self._select)
        self.wait_for(self.drop_down_visible)

    def close_drop_down(self):
        self.parent.execute_script("$(arguments[0]).trigger('chosen:close')", self._select)
        self.wait_for(lambda: not self.drop_down_visible())

    def deselect_all(self):
        """Clear all selected entries."""
        self.wait_until_clickable()
        script = cleandoc(
            """
            var select = arguments[0];
            select.selectedIndex = -1;
            $(select).trigger('chosen:updated').trigger('change');
            """
        )
        self.parent.execute_script(script, self._select)

    def deselect_by_index(self, index):
        """
        Deselect the option at the given index.

        :param index: The option at this index will be deselected
        :type index: int

        throws NoSuchElementException If there is no option with specified index in SELECT
        """
        self.wait_until_clickable()
        script = cleandoc(
            """
            var select = arguments[0];
            var index = arguments[1];
            var success = false;
            if (select.options[index] !== undefined) {
                select.options[index].selected = false;
                $(select).trigger('chosen:updated').trigger('change');
                success = true;
            }
            return success;
            """
        )
        if not self.parent.execute_script(script, self._select, index):
            raise NoSuchElementException("Could not locate element with index {}".format(index))

    def deselect_by_value(self, value):
        """
        Deselect all options that have a value matching the argument.

        That is, when given `'foo'` this would deselect an option like: `<option value='foo'>Bar</option>`

        :param value: The value to match against
        :type value: str | unicode

        throws NoSuchElementException If there is no option with specified value in SELECT
        """
        self.wait_until_clickable()
        script = cleandoc(
            """
            var select = arguments[0];
            var value = arguments[1];
            var success = false;
            for (var i = 0; i < select.options.length; i++) {
                if (select.options[i].value == value) {
                    select.options[i].selected = false;
                    success = true;
                }
            }
            $(select).trigger('chosen:updated').trigger('change');
            return success;
            """
        )
        if not self.parent.execute_script(script, self._select, value):
            raise NoSuchElementException("Cannot locate option with value: {}".format(value))

    def deselect_by_visible_text(self, text):
        """
        Deselect all options that display text matching the argument.

        That is, when given `'Bar'` this would deselect an option like: `<option value='foo'>Bar</option>`

        :param text: The visible text to match against
        :type text: str | unicode

        throws NoSuchElementException If there is no option with specified text in SELECT
        """
        self.wait_until_clickable()
        script = cleandoc(
            """
            var select = arguments[0];
            var text = arguments[1];
            var success = false;
            for (var i = 0; i < select.options.length; i++) {
                if (select.options[i].innerText == text) {
                    select.options[i].selected = false;
                    success = true;
                }
            }
            $(select).trigger('chosen:updated').trigger('change');
            return success;
            """
        )
        if not self.parent.execute_script(script, self._select, text):
            raise NoSuchElementException(
                "Could not locate element with visible text: {}".format(text)
            )

    def select_by_index(self, index):
        """
        Select the option at the given index.

        :param index: The option at this index will be deselected
        :type index: int

        throws NoSuchElementException If there is no option with specified index in SELECT
        """
        self.wait_until_clickable()
        script = cleandoc(
            """
            var select = arguments[0];
            var index = arguments[1];
            var success = false;
            if (select.options[index] !== undefined) {
                select.options[index].selected = true;
                $(select).trigger('chosen:updated').trigger('change');
                success = true;
            }
            return success;
            """
        )
        if not self.parent.execute_script(script, self._select, index):
            raise NoSuchElementException("Could not locate element with index {}".format(index))

    def select_by_value(self, value):
        """
        Select all options that have a value matching the argument.

        That is, when given `'foo'` this would select an option like: `<option value='foo'>Bar</option>`

        :param value: The value to match against
        :type value: str | unicode

        throws NoSuchElementException If there is no option with specified value in SELECT
        """
        self.wait_until_clickable()
        script = cleandoc(
            """
            var select = arguments[0]
            var value = arguments[1]
            var success = false;
            for (var i = 0; i < select.options.length; i++) {
                if (select.options[i].value == value) {
                    select.options[i].selected = true;
                    success = true;
                }
            }
            $(select).trigger('chosen:updated').trigger('change');
            return success;
            """
        )
        if not self.parent.execute_script(script, self._select, value):
            raise NoSuchElementException("Cannot locate option with value: {}".format(value))

    def select_by_visible_text(self, text):
        """
        Select all options that display text matching the argument.

        That is, when given `'Bar'` this would select an option like: `'<option value='foo'>Bar</option>'`

        :param text: The visible text to match against
        :type text: str | unicode

        throws NoSuchElementException If there is no option with specified text in SELECT
        """
        self.wait_until_clickable()
        script = cleandoc(
            """
            var select = arguments[0]
            var text = arguments[1]
            var success = false;
            for (var i = 0; i < select.options.length; i++) {
                if (select.options[i].innerText == text) {
                    select.options[i].selected = true;
                    success = true;
                }
            }
            $(select).trigger('chosen:updated').trigger('change');
            return success;
            """
        )
        if not self.parent.execute_script(script, self._select, text):
            raise NoSuchElementException(
                "Could not locate element with visible text: {}".format(text)
            )

    @property
    def all_selected_options(self):
        return self.select.all_selected_options

    @property
    def first_selected_option(self):
        return self.select.first_selected_option

    @property
    def options(self):
        return self.select.options

    @property
    def options_values(self):
        return [option.get_attribute("value") for option in self.options]

    @property
    def options_texts(self):
        # Selenium's .text property returns empty string for invisible elements
        return [option.get_attribute("text") for option in self.options]

    def is_enabled(self):
        return "chosen-disabled" not in self.get_attribute("class").split()

    def find_parsley_error(self):
        # All the parsley related data attributes are on the original select node
        return self._select.find_parsley_error()


class SingleChosenSelect(_ChosenContainer):
    """A chosen container for a select with single choice"""

    @staticmethod
    def selector(element):
        return (
            element.tag_name == "div"
            and "chosen-container-single" in element.get_attribute("class").split()
        )

    @property
    def selected_option(self):
        return self.first_selected_option

    @property
    def selected_value(self):
        return self.selected_option.get_attribute("value")

    @property
    def selected_text(self):
        # Selenium's .text property returns empty string for invisible elements
        return self.selected_option.get_attribute("text")


class MultiChosenSelect(_ChosenContainer):
    """A chosen container for a select with multiple choices"""

    @staticmethod
    def selector(element):
        return (
            element.tag_name == "div"
            and "chosen-container-multi" in element.get_attribute("class").split()
        )

    @property
    def selected_values(self):
        return [x.get_attribute("value") for x in self.select.all_selected_options]

    @property
    def selected_texts(self):
        return [x.get_attribute("text") for x in self.select.all_selected_options]


class WebElementExtension(object):
    """
    Factory class to produce ExtendedWebElement objects

    You can register extension classes, which will be checked in FIFO
    order for a match of their selector method against the supplied
    Selenium WebElement object. The first matching one will be returned.

    .. code-block::
       :caption: Usage example
       extensions = WebElementExtension(default_element_class=ExtendedWebElement)
       extensions.register_extension(CheckboxInput)
       extended_webelement = extensions(driver.find_element(By.ID, 'SOME-ID'), timeout=10)
    """

    def __init__(self, default_element_class=ExtendedWebElement):
        self._registered_extensions = []
        assert issubclass(default_element_class, ExtendedWebElement)
        self.default_element_class = default_element_class

    def register_extension(self, extension_class):
        assert issubclass(extension_class, ExtendedWebElement)
        self._registered_extensions.append(extension_class)

    def _select_extension(self, web_element, timeout, **kwargs):
        for extension_class in self._registered_extensions:
            if extension_class.selector(web_element):
                return extension_class.from_web_element(
                    web_element, extension_factory=self, timeout=timeout, **kwargs
                )
        return self.default_element_class.from_web_element(
            web_element, extension_factory=self, timeout=timeout, **kwargs
        )

    def __call__(self, web_element, timeout, **kwargs):
        return self._select_extension(web_element=web_element, timeout=timeout, **kwargs)


DEFAULT_EXTENSIONS = WebElementExtension(default_element_class=ExtendedWebElement)
DEFAULT_EXTENSIONS.register_extension(CheckboxInput)
DEFAULT_EXTENSIONS.register_extension(TextInput)
DEFAULT_EXTENSIONS.register_extension(TextArea)
DEFAULT_EXTENSIONS.register_extension(PasswordInput)
DEFAULT_EXTENSIONS.register_extension(RadioButton)
DEFAULT_EXTENSIONS.register_extension(SingleSelect)
DEFAULT_EXTENSIONS.register_extension(MultiSelect)
DEFAULT_EXTENSIONS.register_extension(SingleChosenSelect)
DEFAULT_EXTENSIONS.register_extension(MultiChosenSelect)
DEFAULT_EXTENSIONS.register_extension(NumberInput)