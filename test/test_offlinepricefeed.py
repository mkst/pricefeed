import unittest
from unittest.mock import Mock, patch, call

import quickfix as fix
import quickfix44 as fix44

import app.offlinepricefeed as pf
import app.pxm44 as pxm44

class TestOfflinePriceFeedClass(unittest.TestCase):

    def setUp(self):
        self.queue = Mock()
        self.shutdown_event = Mock()
        self.config = Mock()
        self.config.get = Mock(side_effect=[None])
        self.file_list = Mock()
        # constructor
        self.offlinepricefeed = pf.OfflinePriceFeed(self.queue, self.shutdown_event, self.config, self.file_list)

    # __init__
    def test_constructor(self):
        self.assertEqual(self.queue, self.offlinepricefeed.queue)
        self.assertEqual(self.shutdown_event, self.offlinepricefeed.shutdown_event)
        self.assertEqual(self.config, self.offlinepricefeed.config)
        self.assertEqual(self.file_list, self.offlinepricefeed.file_list)

    def test_init_load_mappings(self):
        self.config.get = Mock(side_effect=['/foo/bar'])
        with patch('os.path.isfile') as isfile:
            isfile = Mock(side_effect=['True'])
            with patch('app.offlinepricefeed.open'):
                with patch('json.load') as json_load:
                    opf = pf.OfflinePriceFeed(self.queue, self.shutdown_event, self.config, self.file_list)
                    json_load.assert_called_once()

    # run
    def test_run(self):
        file1 = Mock()
        file2 = Mock()
        self.offlinepricefeed.file_list = [file1, file2]
        self.offlinepricefeed.shutdown_event.is_set = Mock(side_effect=[False, False])
        with patch('app.offlinepricefeed.OfflinePriceFeed.parse_file') as parse_file:
            with patch('app.offlinepricefeed.OfflinePriceFeed.shutdown') as shutdown:
                self.offlinepricefeed.run()
                calls = [call(file1), call(file2)]
                parse_file.assert_has_calls(calls)
                shutdown.assert_called()

    def test_run(self):
        file1 = Mock()
        file2 = Mock()
        self.offlinepricefeed.file_list = [file1, file2]
        self.offlinepricefeed.shutdown_event.is_set = Mock(side_effect=[True])
        with patch('app.offlinepricefeed.OfflinePriceFeed.parse_file') as parse_file:
            with patch('app.offlinepricefeed.OfflinePriceFeed.shutdown') as shutdown:
                self.offlinepricefeed.run()
                parse_file.assert_called_once_with(file1)
                shutdown.assert_called()

    def test_clean_shutdown(self):
        self.offlinepricefeed.shutdown_event.is_set = Mock(side_effect=[True])
        self.offlinepricefeed.config = Mock()
        self.offlinepricefeed.config.get = Mock(side_effect=[None])
        self.offlinepricefeed.shutdown()
        self.offlinepricefeed.config.get.assert_called_once_with('mappings_path')
        self.offlinepricefeed.shutdown_event.is_set.assert_called_once()

    def test_shutdown_save_mappings(self):
        self.offlinepricefeed.shutdown_event.is_set = Mock(side_effect=[True])
        self.offlinepricefeed.config = Mock()
        self.offlinepricefeed.config.get = Mock(side_effect=['/foo/bar'])
        self.offlinepricefeed.active_subscriptions = 'subs'
        with patch('app.offlinepricefeed.open') as mo:
            with patch('json.dump') as json_dump:
                self.offlinepricefeed.shutdown()
                mo.assert_called_once()
                json_dump.assert_called_once()

    def test_shutdown_trigger_event(self):
        self.offlinepricefeed.shutdown_event.is_set = Mock(side_effect=[False])
        self.offlinepricefeed.config = Mock()
        self.offlinepricefeed.config.get = Mock(side_effect=[None])
        self.offlinepricefeed.shutdown()
        self.offlinepricefeed.shutdown_event.set.assert_called_once()

# parse_fix_line
    def test_to_fix_message(self):
        line = "8=FIX.4.4^9=126^35=i^34=15921156^49=XC461^52=20210401-11:00:00.012^56=Q000^296=1^302=21^295=2^299=0^106=1^188=0.69743^299=2^106=1^188=0.69742^10=188^".replace("^", "\x01")
        msg_type, message = self.offlinepricefeed.to_fix_message(line)
        self.assertEqual('i', msg_type)

    def test_to_fix_message_exception(self):
        line = "8=FIX.4.4^9=125^35=i^34=15921156^49=XC461^52=20210401-11:00:00.012^56=Q000^296=1^302=21^295=2^299=0^106=1^188=0.69743^299=2^106=1^188=0.69742^10=188^".replace("^", "\x01")
        self.assertRaises(fix.InvalidMessage, self.offlinepricefeed.to_fix_message, line)

# parse_nonfix_line
# parse_file
# on_market_data_request
# on_mass_quote
# on_market_data_snapshot
# update_subscriptions
    def test_update_subscriptions_new(self):
        res = self.offlinepricefeed.update_subscriptions(0, 'EURUSD')
        self.assertTrue(res)
        self.assertEqual('EURUSD', self.offlinepricefeed.active_subscriptions.get(0))

    def test_update_subscriptions_update(self):
        # add EURUSD
        self.offlinepricefeed.update_subscriptions(0, 'EURUSD')
        # change to EURJPY
        res = self.offlinepricefeed.update_subscriptions(0, 'EURJPY')
        self.assertTrue(res)
        self.assertEqual('EURJPY', self.offlinepricefeed.active_subscriptions.get(0))

    def test_update_subscriptions_no_change(self):
        # add EURUSD
        self.offlinepricefeed.update_subscriptions(0, 'EURUSD')
        # another EURUSD
        res = self.offlinepricefeed.update_subscriptions(0, 'EURUSD')
        self.assertFalse(res)
        self.assertEqual('EURUSD', self.offlinepricefeed.active_subscriptions.get(0))
