# -*- coding: utf-8 -*-

"""
yapconf.exceptions
~~~~~~~~~~~~~~~~~~

This module contains the set of Yapconf's exceptions.
"""


class YapconfError(Exception):
    """There was an error while handling your config"""
    pass


class YapconfSpecError(YapconfError):
    """There was an error detected in the specification provided"""
    pass


class YapconfLoadError(YapconfError):
    """There was an error while trying to load the overrides provided"""
    pass


class YapconfItemError(YapconfError):
    """There was an error creating a YapconfItem from the specification"""
    pass


class YapconfListItemError(YapconfItemError):
    """There was an error creating a YapconfListItem from the specification"""
    pass


class YapconfDictItemError(YapconfItemError):
    """There was an error creating a YapconfDictItem from the specification"""
    pass


class YapconfItemNotFound(YapconfItemError):
    """We searched through all the overrides and could not find the item"""
    def __init__(self, message, item):
        super(YapconfItemNotFound, self).__init__(message)
        self.item = item


class YapconfValueError(YapconfItemError):
    """We found an item in the overrides but it wasn't what we expected"""
    pass
