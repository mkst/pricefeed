import unittest
from unittest.mock import Mock, patch, call

import quickfix as fix
import quickfix44 as fix44

import app.fixpricefeed as pf
import app.pxm44 as pxm44


class TestPriceFeedClass(unittest.TestCase):

    def setUp(self):
        self.queue = Mock()
        self.shutdown_event = Mock()
        self.fix_adapter = Mock()
        self.pricefeed = pf.FixPriceFeed(self.queue, self.shutdown_event, ["EUR/USD", "USD/JPY"])
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL("spec/pxm44.xml")
        self.fix_mass_quote = fix.Message("8=FIX.4.4|9=135|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|117=1|296=1|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|10=235|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_no_id = fix.Message("8=FIX.4.4|9=129|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|296=1|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|10=230|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_snapshot = fix.Message("8=FIX.4.4|9=163|35=W|34=136232|49=XCT1|52=20200603-12:00:00.106|56=Q004|55=EUR/USD|262=0|268=2|269=0|270=1.11941|271=1000000|299=0|106=1|269=1|270=1.11944|271=1000000|299=0|106=1|10=240|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_request_reject = fix.Message("8=FIX.4.4|9=80|35=Y|34=1567|49=T01|52=20151105-13:08:06.797|56=XCxxx|58=symbol not found|262=0|10=085|".replace("|", "\x01"), self.data_dictionary)

    # __init__
    def test_constructor(self):
        self.assertEqual(self.queue, self.pricefeed.queue)
        self.assertEqual(self.shutdown_event, self.pricefeed.shutdown_event)
        self.assertEqual(["EUR/USD", "USD/JPY"], self.pricefeed.subscriptions)
        self.assertEqual(None, self.pricefeed.fix_adapter)
        self.assertFalse(self.pricefeed.has_ever_logged_on)

    # set_fix_adapter
    def test_set_fix_adapter(self):
        self.pricefeed.set_fix_adapter("fix_adapter")
        self.assertEqual("fix_adapter", self.pricefeed.fix_adapter)

    # on_logon
    def test_onlogon(self):
        with patch('app.fixpricefeed.FixPriceFeed.send_subscriptions') as send_subscriptions:
            self.pricefeed.on_logon(1)
            self.assertEqual(True, self.pricefeed.has_ever_logged_on)
            send_subscriptions.assert_called_with(1)

    # on_logout
    def test_onlogout_no_adapter(self):
        with patch('app.fixpricefeed.FixPriceFeed.shutdown') as shutdown:
            self.pricefeed.has_ever_logged_on = True
            self.pricefeed.on_logout(1)
            shutdown.assert_not_called()

    def test_onlogout_never_logged_on(self):
        with patch('app.fixpricefeed.FixPriceFeed.shutdown') as shutdown:
            self.pricefeed.set_fix_adapter("fix_adapter")
            self.pricefeed.has_ever_logged_on = False
            self.pricefeed.on_logout(1)
            shutdown.assert_not_called()

    def test_onlogout_after_logged_on(self):
        with patch('app.fixpricefeed.FixPriceFeed.shutdown') as shutdown:
            self.pricefeed.set_fix_adapter("fix_adapter")
            self.pricefeed.has_ever_logged_on = True
            self.pricefeed.on_logout(1)
            shutdown.assert_called()

# on_create
# to_admin
# to_app
# from_admin

# run
    def test_run(self):
        self.fix_adapter.isStopped = Mock(side_effect=[False, True])
        self.shutdown_event.is_set = Mock(side_effect=[False, False])
        self.pricefeed.set_fix_adapter(self.fix_adapter)
        with patch("app.fixpricefeed.FixPriceFeed.shutdown") as shutdown:
            self.pricefeed.run()
            shutdown.assert_called()

# shutdown
    def test_shutdown(self):
        self.fix_adapter.isStopped = Mock(side_effect=[False])
        self.shutdown_event.is_set = Mock(side_effect=[False])
        self.pricefeed.set_fix_adapter(self.fix_adapter)
        self.pricefeed.shutdown()
        self.fix_adapter.stop.assert_called_once()
        self.shutdown_event.set.assert_called_once()

# from_app
    def test_from_app_mass_quote(self):
        self.pricefeed.handlers["i"] = Mock()
        self.pricefeed.from_app(self.fix_mass_quote, 1)
        self.pricefeed.handlers["i"].assert_called_once()
        self.assertEqual((self.fix_mass_quote, 1),
                         self.pricefeed.handlers["i"].call_args[0])

    def test_from_app_market_data_snapshot(self):
        self.pricefeed.handlers["W"] = Mock()
        self.pricefeed.from_app(self.fix_market_data_snapshot, 1)
        self.pricefeed.handlers["W"].assert_called_once()
        self.assertEqual((self.fix_market_data_snapshot, 1),
                         self.pricefeed.handlers["W"].call_args[0])

    def test_from_app_market_data_request_reject(self):
        self.pricefeed.handlers["Y"] = Mock()
        self.pricefeed.from_app(self.fix_market_data_request_reject, 1)
        self.pricefeed.handlers["Y"].assert_called_once()
        self.assertEqual((self.fix_market_data_request_reject, 1),
                         self.pricefeed.handlers["Y"].call_args[0])

    def test_from_app_no_handler(self):
        heartbeat = fix44.Heartbeat()
        self.assertRaises(Exception, self.pricefeed.from_app, heartbeat, 1)

    def test_market_data_snapshot(self):
        with patch('app.pricefeed.process_market_data_snapshot', side_effect=[123]) as _:
            self.pricefeed.on_market_data_snapshot(self.fix_market_data_snapshot, None)
            self.pricefeed.queue.put.assert_called_once()
            self.pricefeed.queue.put.assert_called_with(123)

# on_mass_quote
    def test_on_mass_quote_with_quote_id(self):
        with patch('app.pricefeed.process_mass_quote', side_effect=[[123]]) as _:
            with patch('app.fixpricefeed.FixPriceFeed.send_ack') as send_ack:
                self.pricefeed.on_mass_quote(self.fix_mass_quote, None)
                self.pricefeed.queue.put.assert_called_once()
                self.pricefeed.queue.put.assert_called_with(123)
                send_ack.assert_called_with(self.fix_mass_quote, None)

    def test_on_mass_quote_no_quote_id(self):
        with patch('app.pricefeed.process_mass_quote', side_effect=[[123]]) as _:
            with patch('app.fixpricefeed.FixPriceFeed.send_ack') as send_ack:
                self.pricefeed.on_mass_quote(self.fix_mass_quote_no_id, None)
                self.pricefeed.queue.put.assert_called_once()
                self.pricefeed.queue.put.assert_called_with(123)
                send_ack.assert_not_called()

    def test_on_mass_quote_multiple_quotesets(self):
        with patch('app.pricefeed.process_mass_quote', side_effect=[[123, 456]]) as _:
            self.pricefeed.on_mass_quote(self.fix_mass_quote_no_id, None)
            self.assertEqual(2, self.pricefeed.queue.put.call_count)
            calls = [ call(123), call(456) ]
            self.pricefeed.queue.put.assert_has_calls(calls)

# on_market_data_snapshot
    def test_market_data_snapshot(self):
        with patch('app.pricefeed.process_market_data_snapshot', side_effect=[123]) as _:
            self.pricefeed.on_market_data_snapshot(self.fix_market_data_snapshot, None)
            self.pricefeed.queue.put.assert_called_once()
            self.pricefeed.queue.put.assert_called_with(123)

# on_market_data_request_reject
    def test_on_market_data_request_reject(self):
        self.pricefeed.active_subscriptions["0"] = "EURUSD"
        self.pricefeed.on_market_data_request_reject(self.fix_market_data_request_reject, None)
        self.assertEqual(0, len(self.pricefeed.active_subscriptions))

# send_subscriptions
    def test_send_subscription(self):
        with patch('quickfix.Session') as mock_session:
            mock_session.sendToTarget = Mock()
            self.pricefeed.send_subscriptions("session_1")
            self.assertEqual(2, mock_session.sendToTarget.call_count)
            self.assertEqual(2, len(self.pricefeed.active_subscriptions))

# send_ack
    def test_send_ack(self):
        with patch('quickfix.Session') as mock_session:
            mock_session.sendToTarget = Mock()
            self.pricefeed.send_ack(self.fix_mass_quote, 1)
            assert mock_session.sendToTarget.was_called()
            msg = mock_session.sendToTarget.call_args[0]
            self.assertEqual('1', msg[0].getField(117))
