"""Module for the base classes providing the page object modelling."""

import inspect
import os
from abc import ABCMeta, abstractmethod, abstractproperty

import furl
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from six import raise_from

from web_pages.core import elements
from web_pages.core.elements import DEFAULT_EXTENSIONS
from web_pages.core import exceptions


def url_for(path, **kwargs):
    """Get a URL for the current deploy host"""
    scheme = os.getenv("DEPLOY_SCHEME", "https")
    port = os.getenv("DEPLOY_PORT")
    host = os.getenv("DEPLOY_HOST", "www.saucedemo.com")
    f = furl.furl().set(scheme=scheme, host=host, port=port, path=path, **kwargs)
    return f.url


def element(
    locator,
    cache=True,
    timeout=None,
    extension_factory=elements.DEFAULT_EXTENSIONS,
):
    """
    Create a class attribute that represents a WebElement.

    Example usage:

    .. code-block:: python

       class ExamplePage(PageModel):
           input = element((By.CSS_SELECTOR, 'input'))

    :param locator: Tuple for locating the underlying WebElement: (By.<TYPE>, <locator string>)
    :type locator: tuple(string, string)
    :param cache: If `True` the underlying WebElement is cached, set this to `False` for dynamically
        loaded elements that change after the page has loaded.
    :type cache: bool
    :param timeout: Timeout seconds for element interactions, if `None` defaults to page wide
        timeout value.
    :type timeout: None | int | float
    :param extension_factory: Factory class to retrieve extensions for Selenium WebElement
        instances. These provide common interaction models, e.g. simpler text interaction.
    :type extension_factory:
    """
    return _WebElement(
        locator=locator, cache=cache, timeout=timeout, extension_factory=extension_factory
    )



def elements(
    locator,
    cache=True,
    timeout=None,
    extension_factory=elements.DEFAULT_EXTENSIONS,
):
    """
    Create a class attribute that represents a collection of WebElements.

    Example usage:

    .. code-block:: python

       class ExamplePage(PageModel):
           table_cells = elements((By.CSS_SELECTOR, 'td'))


    :param locator: Tuple for locating the underlying WebElement: (By.<TYPE>, <locator string>)
    :type locator: tuple(string, string)
    :param cache: If `True` the underlying WebElement is cached, set this to `False` for dynamically
        loaded elements that change after the page has loaded.
    :type cache: bool
    :param timeout: Timeout seconds for element interactions, if `None` defaults to page wide
        timeout value.
    :type timeout: None | int | float
    :param extension_factory: Factory class to retrieve extensions for Selenium WebElement
        instances. These provide common interaction models, e.g. simpler text interaction.
    """
    return _WebElements(
        locator=locator, cache=cache, timeout=timeout, extension_factory=extension_factory
    )

def fragment(
    page_class,
    root=None,
    cache=True,
    timeout=None,
    extension_factory=DEFAULT_EXTENSIONS,
):
    """
    Create a class attribute that represents a page fragment.

    A page fragment is essentially a page object model that represents only part of a page. This
    makes it possible to separate different areas of concern of a single page into subclasses or
    allows to separate elements that are shared across multiple pages, e.g a navigator bar or a
    footer.

    Example usage:


    .. code-block:: python
       class ExampleFragment(FragmentModel):
           input = element((By.CSS_SELECTOR, 'input'))


       class ExamplePage(PageModel):
           input_dialogue = fragment((By.ID, 'dialogue'), root=element((By.ID, 'dialogue-opened'))

    :param page_class: Class representing the page fragment
    :type page_class: m3d_blackbox.pages.page_model.FragmentModel
    :param root: Optional root element, if not `None` the corresponding fragment element(s) will be
        searched only underneath the HTML node.
    :type root: 
    :param cache: If `True` the underlying WebElement is cached, set this to `False` for dynamically
        loaded elements that change after the page has loaded.
    :type cache: bool
    :param timeout: Timeout seconds for fragment interactions, if `None` it honors the fragment
        class wide timeout level, if a value is supplied it will overwrite the class attribute.
    :type timeout: None | int | float
    :param extension_factory: Factory class to retrieve extensions for Selenium WebElement
        instances. These provide common interaction models, e.g. simpler text interaction.
    :type extension_factory: 
    """
    return _PageFragment(
        page_class=page_class,
        root=root,
        cache=cache,
        timeout=timeout,
        extension_factory=extension_factory,
    )



def fragments(
    page_class,
    roots,
    cache=True,
    timeout=None,
    extension_factory=DEFAULT_EXTENSIONS,
):
    """
    Create a class attribute that represents a collection of page fragments.

    A page fragment is essentially a page object model that represents only part of a page. This
    makes it possible to separate different areas of concern of a single page into subclasses or
    allows to separate elements that are shared across multiple pages, e.g a navigator bar or a
    footer.

    This function makes it easy to represent a collection of repeating fragments, i.e. fragments of
    the same class that have simply different root elements. The page object model will search the
    locator for the `roots` property and create a new fragment for each root WebElement it finds.

    Example usage:

    .. code-block:: python
       class RepeatingFragment(FragmentModel):
           input = element((By.CSS_SELECTOR, 'input'))

       class ExamplePage(PageModel):
           table_fragments = fragments(RepeatingFragment, roots=elements((By.CSS_SELECTOR, 'td'))

    :param page_class: Class representing the page fragment
    :type page_class: m3d_blackbox.pages.page_model.FragmentModel
    :param roots: Collection of root elements, for each underlying WebElement that is found the page
        object will create an instance of the fragment model class with the corresponding root
        element set.
    :type roots:
    :param cache: If `True` the underlying WebElement is cached, set this to `False` for dynamically
        loaded elements that change after the page has loaded.
    :type cache: bool
    :param timeout: Timeout seconds for fragment interactions, if `None` it honors the fragment
        class wide timeout level, if a value is supplied it will overwrite the class attribute.
    :type timeout: None | int | float
    :param extension_factory: Factory class to retrieve extensions for Selenium WebElement
        instances. These provide common interaction models, e.g. simpler text interaction.
    :type extension_factory: 
    """
    return _PageFragments(
        page_class=page_class,
        roots=roots,
        cache=cache,
        timeout=timeout,
        extension_factory=extension_factory,
    )


class _PageObjectModel(object):
    """
    Abstract Base class for all Page Object Models, both pages and fragments.

    The `root` attribute can be a page element or a WebElement, if it's not `None` this will be used
    as the root element when finding page elements. This can be used to restrict locators only to a
    subset of a page, e.g. limit a locator that is used in every table row only to a specific row.

    The `timeout` attribute defines the default timeout for finding and interacting with page
    elements. This can be overwritten on a per element base, when defining the locators.
    """

    __metaclass__ = ABCMeta
    root = None
    timeout = 10

    def __init__(self, driver, timeout=None, root=None):
        self.driver = driver
        if timeout is not None:
            self.timeout = timeout
        if root is not None:
            self.root = root
        self.clear_cached_elements()


    def __getattribute__(self, item):
        attribute = super(_PageObjectModel, self).__getattribute__(item)
        if isinstance(attribute, _PageElement):
            # 'root' page element is special: It is searched from the webdriver directly
            if item == "root":
                return self.driver.find_element(*attribute.locator)
            return attribute(self)
        return attribute


    def find_web_element(self, element_name):
        """
        Bypass cache and web element extensions on page element

        This function should be used sparingly, only if you temporarily want to bypass the
        caching and extended web element object instantiation. Normally you always want to
        simply access the class attribute using `.` lookup, e.g. `test_page.some_element`

        :param element_name: Class attribute name of element to find
        :type element_name: str | unicode
        :return: Returns the WebElement instance of the stored element
        :rtype: selenium.webdriver.remote.webelement.WebElement
        """
        web_element = self.__class__.__dict__[element_name]
        if not isinstance(web_element, _WebElement):
            raise ValueError("{} is not a _WebElement object".format(element_name))
        return web_element.find_web_element(self)


    def find_web_elements(self, element_name):
        """
        Bypass cache and web element extensions on page elements

        This function should be used sparingly, only if you temporarily want to bypass the
        caching and extended web element object instantiation. Normally you always want to
        simply access the class attribute using `.` lookup, e.g. `test_page.some_element`

        :param element_name: Class attribute name of element to find
        :type element_name: str | unicode
        :return: Returns the list of WebElement instances of the stored element
        :rtype: list(selenium.webdriver.remote.webelement.WebElement)
        """
        web_element = self.__class__.__dict__[element_name]
        if not isinstance(web_element, _WebElements):
            raise ValueError("{} is not a _WebElements object".format(element_name))
        return web_element.find_web_elements(self)


    def clear_cached_elements(self):
        """Clear all cached page elements"""
        page_element_members = inspect.getmembers(
            self.__class__, lambda attr: isinstance(attr, _PageElement)
        )
        for member in page_element_members:
            member[1].clear_cache()


    def wait_for(self, wait_fcn, timeout=None, message=""):
        """
        Wait until function returns a *truthy* value

        :param wait_fcn: Function to be evaluated, takes a WebDriver instance as first argument
        :type wait_fcn: Callable
        :param timeout: Timeout for waiting, defaults to page defined timeout
        :type timeout: int | None
        :param message: Message to be displayed, when reaching timeout
        :type message: str | unicode
        :return: Returns the function return value
        :rtype: Any
        """
        if timeout is None:
            timeout = self.timeout
        return WebDriverWait(self.driver, timeout=timeout).until(wait_fcn, message=message)


    def wait_until_loaded(self):
        """
        Wait until page is loaded correctly

        :return: Returns itself
        :rtype: m3d_blackbox.pages.page_model._PageObjectModel
        """
        try:
            self.wait_for(lambda _driver: self.is_loaded())
        except TimeoutException as exc:
            raise_from(
                exceptions.LoadingPageFailed("Failed to load '{}'".format(self)), exc
            )
        self.clear_cached_elements()
        return self


    def is_ajax_complete(self):
        return (
            self.driver.execute_script("return jQuery.active") == 0
            and self.driver.execute_script("return document.readyState") == "complete"
        )


    @abstractmethod
    def is_loaded(self):
        """Assert that the corresponding page is successfully loaded"""
        raise NotImplementedError


class _PageElement(object):
    """
    Base class for elements of page objects defined at class definition time
    This is an internal class and is not be used outside PageBase context
    """


    __metaclass__ = ABCMeta


    def __init__(self, cache, timeout, extension_factory):
        self._cache = None
        self.use_cache = cache
        self.timeout = timeout
        self.extension_factory = extension_factory


    def clear_cache(self):
        self._cache = None


    @abstractmethod
    def __call__(self, parent_page):
        raise NotImplementedError


class _WebElement(_PageElement):
    """
    Represents an extended WebElement of a page object on class definition time
    This is an internal class and is not be used outside _PageObjectModel context
    """

    def __init__(self, locator, **kwargs):
        super(_WebElement, self).__init__(**kwargs)
        self.locator = locator


    def find_web_element(self, parent_page):
        """
        Executes a `find_element` command for the `_WebElement
        This function does not use the cache or any other modifications
        and does return a bare WebElement not the extended subclass.
        :param parent_page: Page object to which this element is attached
        :type parent_page: m3d_blackbox.pages.page_model._PageObjectModel
        :return: Returns the WebElement instance of the stored element
        :rtype: selenium.webdriver.remote.webelement.WebElement
        """
        root = parent_page.driver if parent_page.root is None else parent_page.root
        return root.find_element(*self.locator)


    def __call__(self, parent_page):
        """
        Return the WebElement extension object instance

        :param parent_page: Page object to which this element is attached
        :type parent_page: m3d_blackbox.pages.page_model._PageObjectModel
        :return: The registered extension matching the underlying WebElement
        :rtype: m3d_blackbox.pages.elements.ExtendedWebElement
        """
        if self.use_cache and self._cache:
            return self._cache
        timeout = self.timeout if self.timeout is not None else parent_page.timeout
        selenium_element = self.find_web_element(parent_page)
        extended_element = self.extension_factory(web_element=selenium_element, timeout=timeout)
        if self.use_cache:
            self._cache = extended_element
        return extended_element


class _WebElements(_PageElement):
    """
    Represents a collection of extended WebElements of a page object on class definition time
    This is an internal class and is not be used outside _PageObjectModel context
    """

    def __init__(self, locator, **kwargs):
        super(_WebElements, self).__init__(**kwargs)
        self.locator = locator


    def find_web_elements(self, parent_page):
        """
        Executes a `find_elements` command for the `_WebElement

        This function does not use the cache or any other modifications
        and does return a list of bare WebElements not the extended subclass.

        :param parent_page: Page object to which this element is attached
        :type parent_page: m3d_blackbox.pages.page_model._PageObjectModel
        :return: Returns a list of WebElement instances of the stored element
        :rtype: list(selenium.webdriver.remote.webelement.WebElement)
        """
        root = parent_page.driver if parent_page.root is None else parent_page.root
        return root.find_elements(*self.locator)


    def __call__(self, parent_page):
        """
        Return the list of WebElement extension object instances

        :param parent_page: Page object to which this element is attached
        :type parent_page: m3d_blackbox.pages.page_model._PageObjectModel
        :return: A list of registered extensions matching the underlying WebElements
        :rtype: list(m3d_blackbox.pages.elements.ExtendedWebElement)
        """
        if self.use_cache and self._cache:
            return self._cache
        timeout = self.timeout if self.timeout is not None else parent_page.timeout
        selenium_elements = self.find_web_elements(parent_page)
        extended_elements = [
            self.extension_factory(web_element=el, timeout=timeout) for el in selenium_elements
        ]
        if self.use_cache:
            self._cache = extended_elements
        return extended_elements


    def __getitem__(self, item):
        """
        Method is implemented to satisfy IDEs and linters.
        Upon dynamic retrieval this class will return a list and as such is a subscriptable object.
        """
        raise RuntimeError("Do not retrieve elements directly from this class")


class _PageFragment(_PageElement):
    """
    Represents a page fragment (another page object) of a page object on class definition time
    This is an internal class and is not be used outside _PageObjectModel context
    """


    def __init__(self, page_class, root, **kwargs):
        super(_PageFragment, self).__init__(**kwargs)
        self.page_class = page_class
        self.root = root


    def __call__(self, parent_page):
        """
        Get the page fragment object instance

        :param parent_page: Page object to which this element is attached
        :type parent_page: m3d_blackbox.pages.page_model._PageObjectModel
        :return: The page base object instance representing the page fragment
        :rtype: PageModel
        """
        if self.use_cache and self._cache:
            return self._cache
        page_object = self.page_class(parent_page=parent_page, root=self.root, timeout=self.timeout)
        page_object.wait_until_loaded()
        if self.use_cache:
            self._cache = page_object
        return page_object


class _PageFragments(_PageElement):
    """
    Represents a collection of page fragments of a page with similar `root` values.
    This is an internal class and is not be used outside _PageObjectModel context
    """

    def __init__(self, page_class, roots, **kwargs):
        super(_PageFragments, self).__init__(**kwargs)
        self.page_class = page_class
        self.roots = roots


    def __call__(self, parent_page):
        if self.use_cache and self._cache:
            return self._cache
        page_objects = []
        for root in self.roots.find_web_elements(parent_page):
            page_object = self.page_class(parent_page=parent_page, root=root, timeout=self.timeout)
            page_object.wait_until_loaded()
            page_objects.append(page_object)
        if self.use_cache:
            self._cache = page_objects
        return page_objects


    def __getitem__(self, item):
        """
        Method is implemented to satisfy IDEs and linters.
        Upon dynamic retrieval this class will return a list and as such is a subscriptable object.
        """
        raise RuntimeError("Do not retrieve elements directly from this class")


class PageModel(_PageObjectModel):
    """
    Abstract Base class for all page models

    The `url` attribute should be relative path, the full URL will be used at runtime based on the
    environment variables `DEPLOY_PORT` and `DEPLOY_HOST.

    The `root` attribute can be a page element or a WebElement, if it's not `None` this will be used
    as the root element when finding page elements. This can be used to restrict locators only to a
    subset of a page, e.g. limit a locator that is used in every table row only to a specific row.

    The `timeout` attribute defines the default timeout for finding and interacting with page
    elements. This can be overwritten on a per element base, when defining the locators.

    The directory of the page object should correspond to the paths of the underlying page.

    Example of usage:

    .. code-block:: python

        class LoginPage(PageBase):
            url = "/auth/login"

            username = element((By.ID, "username"))
            password = element((By.ID, "password"))
    """


    def __init__(self, driver, load_page=True, **kwargs):
        super(PageModel, self).__init__(driver=driver, **kwargs)
        if load_page:
            self.load_page()


    def __str__(self):
        return "{} with url:{}".format(self.__class__.__name__, self.url)


    @abstractproperty
    def url(self):
        """
        The url of the underlying web-page.

        .. warning::
           This should be overwritten as a class level attribute
        """
        raise NotImplementedError


    def load_page(self, force_reload=False):
        """
        Load the page.


        Navigate the web driver to url of the page and wait for it
        to load. If the Page Object is a fragment (e.g. navigation bar), then the URL should
        be `None`, and this function will only wait until the fragment is properly loaded.


        :param force_reload: If True this will reload the page even if we are already on that page
        :type force_reload: bool
        """
        if self.url and (force_reload or self.driver.current_url != url_for(self.url)):
            self.driver.get(url_for(self.url))
        self.wait_until_loaded()


    @abstractmethod
    def is_loaded(self):
        """Assert that the corresponding page is successfully loaded"""
        return self.driver.current_url == url_for(self.url)



class FragmentModel(_PageObjectModel):
    """
    Abstract Base class for partial pages also called page fragments.

    The `root` attribute can be a page element or a WebElement, if it's not `None` this will be used
    as the root element when finding page elements. This can be used to restrict locators only to a
    subset of a page, e.g. limit a locator that is used in every table row only to a specific row.

    The `timeout` attribute defines the default timeout for finding and interacting with page
    elements. This can be overwritten on a per element base, when defining the locators.

    Use this class to group interaction elements, e.g. a modal dialogue,
    or to represent shared parts of pages, e.g. a navigation bar.

    Example of usage:
    .. code-block:: python


        class PopupDialogue(FragmentModel):
            submit_button = element((By.ID, "submit"))


        class LoginPage(PageBase):
            url = "/auth/login"
            submit_popup = fragment(PopupDialogue)

    """


    def __init__(self, parent_page, **kwargs):
        self.parent = parent_page
        super(FragmentModel, self).__init__(driver=parent_page.driver, **kwargs)


    def __str__(self):
        return "{} with parent:{}".format(self.__class__.__name__, self.parent)


    @abstractmethod
    def is_loaded(self):
        """Assert that the corresponding fragment is loaded"""
        raise NotImplementedError