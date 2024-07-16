class NoneValueException(Exception):
    """Exception raised for a missing token or environment variable."""


class UndefinedStatusException(Exception):
    """Exception raised for no expected status."""


class StatusCodeException(Exception):
    """Exception raised if HTTP request code status is not 200."""


class SendTelegramException(Exception):
    """Exception raised because the message to user was not sent."""
