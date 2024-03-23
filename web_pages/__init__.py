"""
A page object is an object-oriented class that serves as an interface to a page of your
application. The tests then use the methods of this page object class whenever they need to
interact with the UI of that page. The page object model itself contains all definitions
of user relevant page elements and provides methods to simplify the core interaction
flows the page offers. They should serve as a single repository for the services or
operations offered by the page rather relying on scattered test classes to provide these.

This allows for clear separation between test code and page specific code such as locators. If any
UI changes are implemented there should be only one place, this place where changes are necessary.

Page objects can be thought of as facing in two directions simultaneously. Facing towards the
developer of a test, they represent the services offered by a particular page. Facing away from
the developer, they should be the only thing that has a deep knowledge of the structure of the HTML
of a page (or part of a page). It's simplest to think of the methods on a page object as offering
the "services" that a page offers rather than exposing the details and mechanics of the page.

Page objects themselves should never make any verifications or assertions themselves (with
a few exceptions like checking if the correct page is loaded). The page object should model
and contain the representation of the page and offer a way to access the services the page
provides. But no code related to what's being tested should be within the page object.

And in the same way a UI test should never rely on specific internals of the web page
it's testing. If an HTML node is added or an attribute is changed, the necessary page
object needs updating, but the UI test should stay the same. That means if you use
`driver.find_element(...)` in your UI test you are not properly using page object models.

A page object does not necessarily need to model a whole page, it can model
a component of a page that is not a part of a specific page, for example a
navigation bar, or you can split a very complex page into multiple components.

See also: https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/
"""