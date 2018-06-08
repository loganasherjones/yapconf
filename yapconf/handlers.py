# -*- coding: utf-8 -*-
import copy

from watchdog.events import RegexMatchingEventHandler

import yapconf
from yapconf.exceptions import YapconfLoadError, YapconfSourceError


class ConfigChangeHandler(object):
    """Handles config changes.

    Expects a watcher to call it when a particular config changes.
    """

    def __init__(self, current_config, spec, user_handler=None):
        # We perform a deep copy so that we can accurately assess whether
        # or not the value has changed for in-memory dictionaries.
        self.current_config = copy.deepcopy(current_config)
        self.spec = spec
        self.user_handler = user_handler

    def handle_config_change(self, new_config):
        """Handle the new configuration.

        Args:
            new_config (dict): The new configuration

        """
        if self.user_handler:
            self.user_handler(self.current_config, new_config)
        self._call_spec_handlers(new_config)
        self.current_config = copy.deepcopy(new_config)

    def _call_spec_handlers(self, new_config):
        flattened_config = yapconf.flatten(new_config, self.spec._separator)
        flattened_current = yapconf.flatten(
            self.current_config, self.spec._separator
        )

        for key, value in flattened_config.items():
            if value != flattened_current.get(key):
                item = self.spec.find_item(key)
                if item and item.watch_target:
                    item.watch_target(flattened_current[key], value)


class FileHandler(RegexMatchingEventHandler):
    """Watchdog handler that only watches a specific file."""

    def __init__(self, filename, handler, file_type='json'):
        super(FileHandler, self).__init__(regexes=[r'^%s$' % filename])
        self._handler = handler
        self._filename = filename
        self._file_type = file_type

    def on_deleted(self, event):
        raise YapconfSourceError(
            'While watching file %s the file was deleted. Aborting watch.'
            % self._filename
        )

    def on_modified(self, event):
        new_config = self._load_config(self._filename)
        self._handler.handle_config_change(new_config)

    def _load_config(self, filename):
        return yapconf.load_file(
            filename,
            file_type=self._file_type,
            klazz=YapconfLoadError
        )
