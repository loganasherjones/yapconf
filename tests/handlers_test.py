# -*- coding: utf-8 -*-
import pytest
from mock import Mock, patch

from yapconf.exceptions import YapconfSourceError
from yapconf.handlers import ConfigChangeHandler, FileHandler


def test_handle_config_change(simple_spec):
    current_config = {'my_string': 'foo'}
    new_config = {'my_string': 'bar'}
    user_handler = Mock()
    item_handler = Mock()

    handler = ConfigChangeHandler(
        current_config, simple_spec, user_handler
    )

    item = simple_spec.find_item('my_string')
    item.watch_target = item_handler

    handler.handle_config_change(current_config)
    user_handler.assert_called_with(current_config, current_config)
    assert item_handler.call_count == 0

    handler.handle_config_change(new_config)
    assert item_handler.call_count == 1


def test_handle_config_change_too_many_items(simple_spec):
    current_config = {'my_string': 'foo'}
    new_config = {'NOT_IN_SPEC': 'bar'}
    user_handler = Mock()
    item_handler = Mock()

    handler = ConfigChangeHandler(
        current_config, simple_spec, user_handler
    )

    item = simple_spec.find_item('my_string')
    item.watch_target = item_handler

    handler.handle_config_change(new_config)
    user_handler.assert_called_with(current_config, new_config)
    assert item_handler.call_count == 0


def test_file_handler():
    custom_handler = Mock()
    handler = FileHandler('filename', custom_handler)

    with patch('yapconf.load_file') as mock_load:
        mock_load.return_value = "new_config"
        handler.on_modified(None)
        custom_handler.handle_config_change.assert_called_with('new_config')


def test_file_handler_on_deleted():
    handler = FileHandler('filename', Mock())
    with pytest.raises(YapconfSourceError):
        handler.on_deleted(None)
