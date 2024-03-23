from selenium.common.exceptions import TimeoutException

class LoadingPageFailed(TimeoutException):
    """Failed to load page."""

    pass