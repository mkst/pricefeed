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
        # data dictionary
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL("spec/pxm44.xml")

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

    def test_init_safe_mode(self):
        config = Mock()
        config.get = Mock(side_effect=[None])
        self.offlinepricefeed = pf.OfflinePriceFeed(Mock(), Mock(), config, Mock(), safe_mode=True)
        self.assertTrue(self.offlinepricefeed.safe_mode)


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

# to_fix_message
    def test_to_fix_message(self):
        line = "8=FIX.4.4^9=126^35=i^34=15921156^49=XC461^52=20210401-11:00:00.012^56=Q000^296=1^302=21^295=2^299=0^106=1^188=0.69743^299=2^106=1^188=0.69742^10=188^".replace("^", "\x01")
        msg_type, message = self.offlinepricefeed.to_fix_message(line)
        self.assertEqual('i', msg_type)

    def test_to_fix_message_exception(self):
        line = "8=FIX.4.4^9=125^35=i^34=15921156^49=XC461^52=20210401-11:00:00.012^56=Q000^296=1^302=21^295=2^299=0^106=1^188=0.69743^299=2^106=1^188=0.69742^10=188^".replace("^", "\x01")
        self.assertRaises(fix.InvalidMessage, self.offlinepricefeed.to_fix_message, line)

# parse_fix_line
    def test_parse_fix_line_snapshot(self):
        snapshot_handler = Mock()
        line = "8=FIX.4.4^9=92^35=W^55=UT100^262=UT100^268=2^269=0^270=235.1^271=58.8^299=0^269=1^270=234.9^271=58.8^299=0^10=068^".replace("^", "\x01")
        time = 1621515600453000 # 2021-05-20 13:00:00.453

        self.offlinepricefeed.handlers['W'] = snapshot_handler
        self.offlinepricefeed.parse_fix_line(line, time)
        snapshot_handler.assert_called_once()

    def test_parse_fix_line_no_handler(self):
        # remove snapshot handler
        del(self.offlinepricefeed.handlers['W'])
        line = "8=FIX.4.4^9=92^35=W^55=UT100^262=UT100^268=2^269=0^270=235.1^271=58.8^299=0^269=1^270=234.9^271=58.8^299=0^10=068^".replace("^", "\x01")
        time = 1621515600453000 # 2021-05-20 13:00:00.453
        with self.assertLogs('app.offlinepricefeed', level='WARNING') as logger_warning:
            self.offlinepricefeed.parse_fix_line(line, time)
            self.assertEqual("WARNING:app.offlinepricefeed:Unsupported MsgType received W", logger_warning.output[0][:59])

    def test_parse_fix_line_bad_fix_message(self):
        snapshot_handler = Mock()
        # wrong BodyLength
        line = "8=FIX.4.4^9=93^35=W^55=UT100^262=UT100^268=2^269=0^270=235.1^271=58.8^299=0^269=1^270=234.9^271=58.8^299=0^10=068^".replace("^", "\x01")
        time = 1621515600453000 # 2021-05-20 13:00:00.453
        self.offlinepricefeed.handlers['W'] = snapshot_handler
        self.offlinepricefeed.parse_fix_line(line, time)
        snapshot_handler.assert_not_called()

# parse_nonfix_line
    def test_parse_nonfix_line_info(self):
        line = '2021-05-20 13:00:00.453|920926 [INFO ] test123'
        with self.assertLogs('app.offlinepricefeed', level='INFO') as logger_info:
            self.offlinepricefeed.parse_nonfix_line(line)
            self.assertEqual("INFO:app.offlinepricefeed:NON-FIX line: '[INFO ] test123'", logger_info.output[0])

    def test_parse_nonfix_line_warning(self):
        line = '2021-05-20 13:00:00.453|920926 [ERROR] test123'
        with self.assertLogs('app.offlinepricefeed', level='WARNING') as logger_warning:
            self.offlinepricefeed.parse_nonfix_line(line)
            self.assertEqual("WARNING:app.offlinepricefeed:NON-FIX line: '2021-05-20 13:00:00.453|920926 [ERROR] test123'", logger_warning.output[0])

# parse_file
    def test_parse_file(self):
        line = '2021-05-20 13:00:00.453|920926 [INFO ] 8=FIX.4.4^9=92^35=W^55=UT100^262=UT100^268=2^269=0^270=235.1^271=58.8^299=0^269=1^270=234.9^271=58.8^299=0^10=068^'.replace("^", "\x01")
        file = Mock()
        file.name = "testfile"
        file.readlines.side_effect = [[line]]
        with patch('app.offlinepricefeed.OfflinePriceFeed.parse_fix_line') as parse_fix_line:
            self.offlinepricefeed.parse_file(file)
            parse_fix_line.assert_called_once()
            parse_fix_line.assert_called_with('8=FIX.4.4^9=92^35=W^55=UT100^262=UT100^268=2^269=0^270=235.1^271=58.8^299=0^269=1^270=234.9^271=58.8^299=0^10=068^'.replace("^", "\x01"), 1621515600453000)

    def test_parse_file_invalid_time(self):
        line = '2021-05-20T13:00:00.453|920926 [INFO ] 8=FIX.4.4^9=92^35=W^55=UT100^262=UT100^268=2^269=0^270=235.1^271=58.8^299=0^269=1^270=234.9^271=58.8^299=0^10=068^'.replace("^", "\x01")
        file = Mock()
        file.name = "testfile"
        file.readlines.side_effect = [[line]]
        with patch('app.offlinepricefeed.OfflinePriceFeed.parse_fix_line') as parse_fix_line:
            self.offlinepricefeed.parse_file(file)
            parse_fix_line.assert_called_once()
            parse_fix_line.assert_called_with('8=FIX.4.4^9=92^35=W^55=UT100^262=UT100^268=2^269=0^270=235.1^271=58.8^299=0^269=1^270=234.9^271=58.8^299=0^10=068^'.replace("^", "\x01"), 0)

    def test_parse_file_empty_line(self):
        line = ''
        file = Mock()
        file.name = "testfile"
        file.readlines.side_effect = [[line]]
        with patch('app.offlinepricefeed.OfflinePriceFeed.parse_fix_line') as parse_fix_line:
            with patch('app.offlinepricefeed.OfflinePriceFeed.parse_nonfix_line') as parse_nonfix_line:
                self.offlinepricefeed.parse_file(file)
                parse_fix_line.assert_not_called()
                parse_nonfix_line.assert_not_called()

    def test_parse_file_nonfix_line(self):
        line = 'TEST'
        file = Mock()
        file.name = "testfile"
        file.readlines.side_effect = [[line]]
        with patch('app.offlinepricefeed.OfflinePriceFeed.parse_fix_line') as parse_fix_line:
            with patch('app.offlinepricefeed.OfflinePriceFeed.parse_nonfix_line') as parse_nonfix_line:
                self.offlinepricefeed.parse_file(file)
                parse_fix_line.assert_not_called()
                parse_nonfix_line.assert_called_once()

# on_market_data_request
    def test_on_market_data_request(self):
        message = fix.Message("8=FIX.4.4^9=112^35=V^34=2^49=Q000^52=20210328-21:00:00.516^56=XC461^262=0^263=1^264=16^265=1^146=1^55=EUR/USD^267=2^269=0^269=1^10=117^".replace("^", "\x01"), self.data_dictionary)
        time = 0
        with patch('app.offlinepricefeed.OfflinePriceFeed.update_subscriptions') as update_subscriptions:
            with patch('app.pricefeed.clear_book') as clear_book:
                self.offlinepricefeed.on_market_data_request(message, time)
                update_subscriptions.assert_called_once()
                update_subscriptions.assert_called_with('0', 'EURUSD')
                clear_book.assert_called_once()
                clear_book.assert_called_with=('EURUSD')


# on_mass_quote
    def test_on_mass_quote(self):
        message = fix.Message("8=FIX.4.4^9=126^35=i^34=15921156^49=XC461^52=20210401-11:00:00.012^56=Q000^296=1^302=21^295=2^299=0^106=1^188=0.69743^299=2^106=1^188=0.69742^10=188^".replace("^", "\x01"), self.data_dictionary)
        time = 1621515600453000
        with patch('app.pricefeed.process_mass_quote', side_effect=[[123]]) as process_mass_quote:
            self.offlinepricefeed.safe_mode = False
            self.offlinepricefeed.on_mass_quote(message, time)
            process_mass_quote.assert_called_once()
            process_mass_quote.assert_called_with(message, {}, message_time=time, offline=True, hardcoded_provider=None)
            self.queue.put.assert_called_once()
            self.queue.put.assert_called_with(123)

    def test_on_mass_quote_safe_mode(self):
        message = fix.Message("8=FIX.4.4^9=155^35=i^296=2^302=EUR/USD^295=1^299=0^134=1000000^135=1000000^188=1.22015^190=1.22016^302=USD/CAD^295=1^299=0^134=1000000^135=1000000^188=1.21100^190=1.21105^10=143^".replace("^", "\x01"), self.data_dictionary)
        time = 1621515600453000
        quotes = (0, 'EURUSD', [123])
        with patch('app.pricefeed.process_mass_quote', side_effect=[[quotes]]) as process_mass_quote:
            self.offlinepricefeed.safe_mode = True
            self.offlinepricefeed.snapshots = {'EURUSD':True}
            self.offlinepricefeed.on_mass_quote(message, time)
            process_mass_quote.assert_called_once()
            process_mass_quote.assert_called_with(message, {}, message_time=time, offline=True, hardcoded_provider=None)
            self.queue.put.assert_called_once()
            self.queue.put.assert_called_with(quotes)

    def test_on_mass_quote_safe_mode_no_snapshot(self):
        message = fix.Message("8=FIX.4.4^9=155^35=i^296=2^302=EUR/USD^295=1^299=0^134=1000000^135=1000000^188=1.22015^190=1.22016^302=USD/CAD^295=1^299=0^134=1000000^135=1000000^188=1.21100^190=1.21105^10=143^".replace("^", "\x01"), self.data_dictionary)
        time = 1621515600453000
        quotes = (0, 'EURUSD', [123])
        with patch('app.pricefeed.process_mass_quote', side_effect=[[quotes]]) as process_mass_quote:
            self.offlinepricefeed.safe_mode = True
            self.offlinepricefeed.snapshots = {}
            self.offlinepricefeed.on_mass_quote(message, time)
            process_mass_quote.assert_called_once()
            process_mass_quote.assert_called_with(message, {}, message_time=time, offline=True, hardcoded_provider=None)
            self.queue.put.assert_not_called()

# on_market_data_snapshot
    def test_on_market_data_snapshot(self):
        message = fix.Message("8=FIX.4.4^9=107^35=W^55=EUR/GBP^262=EUR/GBP^268=2^269=0^270=1.02732^271=200287.1^299=0^269=1^270=1.0275^271=200287.1^299=0^10=244^".replace("^", "\x01"), self.data_dictionary)
        time = 1621515600453000
        with patch('app.offlinepricefeed.OfflinePriceFeed.update_subscriptions') as update_subscriptions:
            with patch('app.pricefeed.process_market_data_snapshot', side_effect=[123]) as process_mass_quote:
                self.offlinepricefeed.on_market_data_snapshot(message, time)
                update_subscriptions.assert_called_once()
                update_subscriptions.assert_called_with('EUR/GBP', 'EURGBP')
                self.queue.put.assert_called_once()
                self.queue.put.assert_called_with(123)

    def test_on_market_data_snapshot_safe_mode(self):
        message = fix.Message("8=FIX.4.4^9=107^35=W^55=EUR/GBP^262=EUR/GBP^268=2^269=0^270=1.02732^271=200287.1^299=0^269=1^270=1.0275^271=200287.1^299=0^10=244^".replace("^", "\x01"), self.data_dictionary)
        time = 1621515600453000
        with patch('app.offlinepricefeed.OfflinePriceFeed.update_subscriptions') as update_subscriptions:
            with patch('app.pricefeed.process_market_data_snapshot', side_effect=[123]) as process_mass_quote:
                self.offlinepricefeed.safe_mode = True
                self.offlinepricefeed.snapshots = {}
                self.offlinepricefeed.on_market_data_snapshot(message, time)
                update_subscriptions.assert_called_once()
                update_subscriptions.assert_called_with('EUR/GBP', 'EURGBP')
                self.queue.put.assert_called_once()
                self.queue.put.assert_called_with(123)
                self.assertTrue(self.offlinepricefeed.snapshots['EURGBP'])

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
