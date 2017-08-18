"""
    zoom.exceptions

    System wide exceptions
"""


class SystemException(Exception):
    pass


class PageMissingException(Exception):
    pass


class DatabaseException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


class ValidException(Exception):
    """invalid record"""
    pass


class TypeException(Exception):
    """unsupported type"""
    pass

class DatabaseMissingException(Exception):
    """Database not found"""
    pass

class SiteMissingException(Exception):
    """Site directory not found"""
    pass

class ConfigFileMissingException(Exception):
    """Site config not found"""
    pass
