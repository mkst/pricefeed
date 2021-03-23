import unittest
from unittest.mock import Mock, patch, call

import quickfix as fix
import quickfix44 as fix44

import app.pricefeed as pf
import app.pxm44 as pxm44


class TestPriceFeedClass(unittest.TestCase):

    def setUp(self):
        self.queue = Mock()
        self.shutdown_event = Mock()
        self.fix_adapter = Mock()
        self.pricefeed = pf.PriceFeed(self.queue, self.shutdown_event, ["EUR/USD", "USD/JPY"])
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL("spec/pxm44.xml")
        self.fix_mass_quote = fix.Message("8=FIX.4.4|9=135|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|117=1|296=1|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|10=235|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_no_id = fix.Message("8=FIX.4.4|9=129|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|296=1|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|10=230|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_quotesets = fix.Message("8=FIX.4.4|9=201|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|296=2|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|302=1|295=1|299=0|106=2|134=2000000|135=2000000|188=2.51218|190=2.51223|10=208|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_snapshot = fix.Message("8=FIX.4.4|9=163|35=W|34=136232|49=XCT1|52=20200603-12:00:00.106|56=Q004|55=EUR/USD|262=0|268=2|269=0|270=1.11941|271=1000000|299=0|106=1|269=1|270=1.11944|271=1000000|299=0|106=1|10=240|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_snapshot_zero_qty = fix.Message("8=FIX.4.4|9=153|35=W|34=848278|49=XC461|52=20210318-21:00:16.225|56=Q003|55=XAU/USD|262=51|268=2|269=0|270=1735.98|271=0|299=0|106=2|269=1|270=1737.04|271=0|299=0|106=2|10=047|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_request_reject = fix.Message("8=FIX.4.4|9=80|35=Y|34=1567|49=T01|52=20151105-13:08:06.797|56=XCxxx|58=symbol not found|262=0|10=085|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_large = fix.Message("8=FIX.4.4|9=3325|35=i|34=11|49=XC461|52=20210316-14:58:50.329|56=Q003|296=9|302=37|295=6|299=0|106=0|134=1000000|135=1000000|188=7.76648|190=7.76668|299=1|106=0|134=3000000|135=3000000|188=7.76645|190=7.7667|299=2|106=0|134=5000000|135=5000000|188=7.76643|190=7.76673|299=3|106=0|134=10000000|135=10000000|188=7.76637|190=7.7668|299=4|106=2|134=8000000|135=8000000|188=7.76633|190=7.76683|299=5|106=0|134=25000000|135=25000000|188=7.76618|190=7.767|302=38|295=6|299=0|106=2|134=2800000|135=3600000|188=308.355|190=308.555|299=1|106=2|134=3100000|135=3800000|188=308.354|190=308.556|299=2|106=2|134=3300000|135=3900000|188=308.353|190=308.557|299=3|106=2|134=3600000|135=4100000|188=308.352|190=308.558|299=4|106=2|134=3900000|135=6100000|188=308.351|190=308.559|299=5|106=0|134=1000000|135=1000000|188=308.29|190=308.61|302=39|295=6|299=0|106=0|134=1000000|135=1000000|188=3.2997|190=3.3016|299=1|106=0|134=2000000|135=2000000|188=3.2996|190=3.3017|299=2|106=0|134=1000000|135=3000000|188=3.2995|190=3.3018|299=3|106=0|134=3000000|135=4000000|188=3.2994|190=3.3019|299=4|106=0|134=4000000|135=5000000|188=3.2993|190=3.302|299=5|106=1|134=5000000|135=1000000|188=3.2992|190=3.3021|302=40|295=6|299=0|106=2|134=4000000|135=4000000|188=108.899|190=108.901|299=1|106=1|134=3000000|135=1000000|188=108.898|190=108.901|299=2|106=1|134=1000000|135=3000000|188=108.898|190=108.902|299=3|106=1|134=5000000|135=5000000|188=108.897|190=108.903|299=4|106=2|134=5000000|135=5000000|188=108.896|190=108.903|299=5|106=1|134=1000000|135=10000000|188=108.896|190=108.904|302=41|295=6|299=0|106=2|134=1000000|135=300000|188=20.5538|190=20.55849|299=1|106=2|134=1000000|135=750000|188=20.5535|190=20.55857|299=2|106=2|134=300000|135=1500000|188=20.55349|190=20.5588|299=3|106=2|134=750000|135=2250000|188=20.55343|190=20.55902|299=4|106=2|134=1500000|135=3000000|188=20.55326|190=20.55921|299=5|106=1|134=2000000|135=1000000|188=20.5532|190=20.5593|302=42|295=6|299=0|106=2|134=1000000|135=1000000|188=8.47478|190=8.47578|299=1|106=2|134=1600000|135=1500000|188=8.4745|190=8.47606|299=2|106=2|134=2000000|135=2100000|188=8.47441|190=8.47633|299=3|106=2|134=2600000|135=4100000|188=8.47429|190=8.47668|299=4|106=2|134=2900000|135=4600000|188=8.47424|190=8.47672|299=5|106=0|134=2000000|135=1000000|188=8.4736|190=8.477|302=43|295=6|299=0|106=2|134=600000|135=600000|188=3.8563|190=3.8568|299=1|106=2|134=1200000|135=1100000|188=3.85619|190=3.85689|299=2|106=2|134=1700000|135=1700000|188=3.85615|190=3.85693|299=3|106=2|134=3700000|135=2300000|188=3.85608|190=3.85698|299=4|106=2|134=4300000|135=2900000|188=3.85607|190=3.85702|299=5|106=0|134=1000000|135=1000000|188=3.8559|190=3.8575|302=45|295=5|299=0|106=1|134=1000000|135=1000000|188=72.689|190=72.7084|299=1|106=1|134=1000000|135=3000000|188=72.6848|190=72.7119|299=2|106=2|134=3000000|135=1000000|188=72.6813|190=72.715|299=3|106=1|134=5000000|135=5000000|188=72.6712|190=72.719|299=4|106=1|134=6000000|135=6000000|188=72.6672|190=72.7229|302=46|295=6|299=0|106=2|134=1000000|135=1000000|188=8.522|190=8.5232|299=1|106=2|134=3000000|135=1500000|188=8.5218|190=8.52335|299=2|106=2|134=1000000|135=1600000|188=8.5217|190=8.52337|299=3|106=2|134=1600000|135=2100000|188=8.52158|190=8.52345|299=4|106=1|134=2600000|135=1000000|188=8.5215|190=8.5235|299=5|106=2|134=3100000|135=4600000|188=8.52147|190=8.52367|10=166|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_snapshot_gbpusd = fix.Message("8=FIX.4.4|9=333|35=W|34=118004|49=XC461|52=20210323-18:30:03.059|56=Q003|55=GBP/USD|262=27|268=6|269=0|270=1.37652|271=1000000|299=1|106=1|269=0|270=1.37651|271=3000000|299=2|106=1|269=0|270=1.37649|271=5000000|299=0|106=1|269=1|270=1.37651|271=4000000|299=1|106=2|269=1|270=1.37655|271=1000000|299=0|106=0|269=1|270=1.37658|271=1000000|299=2|106=1|10=155|".replace("|", "\x01"), self.data_dictionary)

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
        with patch('app.pricefeed.PriceFeed.send_subscriptions') as send_subscriptions:
            self.pricefeed.on_logon(1)
            self.assertEqual(True, self.pricefeed.has_ever_logged_on)
            send_subscriptions.assert_called_with(1)

    # on_logout
    def test_onlogout_no_adapter(self):
        with patch('app.pricefeed.PriceFeed.shutdown') as shutdown:
            self.pricefeed.has_ever_logged_on = True
            self.pricefeed.on_logout(1)
            shutdown.assert_not_called()

    def test_onlogout_never_logged_on(self):
        with patch('app.pricefeed.PriceFeed.shutdown') as shutdown:
            self.pricefeed.set_fix_adapter("fix_adapter")
            self.pricefeed.has_ever_logged_on = False
            self.pricefeed.on_logout(1)
            shutdown.assert_not_called()

    def test_onlogout_after_logged_on(self):
        with patch('app.pricefeed.PriceFeed.shutdown') as shutdown:
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
        with patch("app.pricefeed.PriceFeed.shutdown") as shutdown:
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

# on_mass_quote
    def test_on_mass_quote_with_quote_id(self):
        with patch('app.pricefeed.PriceFeed.send_ack') as send_ack:
            self.pricefeed.active_subscriptions["0"] = "EURUSD"
            self.pricefeed.on_mass_quote(self.fix_mass_quote, None)
            self.pricefeed.queue.put.assert_called_once()
            self.pricefeed.queue.put.assert_called_with((1447100433240000, 'EURUSD', [['0', 1000000.0, 1000000.0, 1.51218, 1.51223, '1', '1']], False))
            send_ack.assert_called_with(self.fix_mass_quote, None)

    def test_on_mass_quote_no_quote_id(self):
        with patch('app.pricefeed.PriceFeed.send_ack') as send_ack:
            self.pricefeed.active_subscriptions["0"] = "EURUSD"
            self.pricefeed.on_mass_quote(self.fix_mass_quote_no_id, None)
            self.pricefeed.queue.put.assert_called_once()
            self.pricefeed.queue.put.assert_called_with((1447100433240000, 'EURUSD', [['0', 1000000.0, 1000000.0, 1.51218, 1.51223, '1', '1']], False))
            send_ack.assert_not_called()

    def test_on_mass_quote_multiple_quotesets(self):
        self.pricefeed.active_subscriptions["0"] = "EURUSD"
        self.pricefeed.active_subscriptions["1"] = "AUDCAD"
        self.pricefeed.on_mass_quote(self.fix_mass_quote_quotesets, None)
        assert (self.pricefeed.queue.put.call_count == 2)
        calls = [
            call((1447100433240000, 'EURUSD', [['0', 1000000.0, 1000000.0, 1.51218, 1.51223, '1', '1']], False)),
            call((1447100433240000, 'AUDCAD', [['0', 2000000.0, 2000000.0, 2.51218, 2.51223, '2', '2']], False))
        ]
        self.pricefeed.queue.put.assert_has_calls(calls)

    def test_on_mass_quote_large_quotesets(self):
        self.pricefeed.active_subscriptions["37"] = "USDHKD"
        self.pricefeed.active_subscriptions["38"] = "USDHUF"
        self.pricefeed.active_subscriptions["39"] = "USDILS"
        self.pricefeed.active_subscriptions["40"] = "USDJPY"
        self.pricefeed.active_subscriptions["41"] = "USDMXN"
        self.pricefeed.active_subscriptions["42"] = "USDNOK"
        self.pricefeed.active_subscriptions["43"] = "USDPLN"
        self.pricefeed.active_subscriptions["45"] = "USDRUB"
        self.pricefeed.active_subscriptions["46"] = "USDSEK"
        self.pricefeed.on_mass_quote(self.fix_mass_quote_large, None)
        assert (self.pricefeed.queue.put.call_count == 9)
        calls = [
            call((1615906730329000, 'USDHKD', [
                ['0', 1000000.0, 1000000.0, 7.76648, 7.76668, '0', '0'],
                ['1', 3000000.0, 3000000.0, 7.76645, 7.7667, '0', '0'],
                ['2', 5000000.0, 5000000.0, 7.76643, 7.76673, '0', '0'],
                ['3', 10000000.0, 10000000.0, 7.76637, 7.7668, '0', '0'],
                ['4', 8000000.0, 8000000.0, 7.76633, 7.76683, '2', '2'],
                ['5', 25000000.0, 25000000.0, 7.76618, 7.767, '0', '0']
            ], False)),
            call((1615906730329000, 'USDHUF', [
                ['0', 2800000.0, 3600000.0, 308.355, 308.555, '2', '2'],
                ['1', 3100000.0, 3800000.0, 308.354, 308.556, '2', '2'],
                ['2', 3300000.0, 3900000.0, 308.353, 308.557, '2', '2'],
                ['3', 3600000.0, 4100000.0, 308.352, 308.558, '2', '2'],
                ['4', 3900000.0, 6100000.0, 308.351, 308.559, '2', '2'],
                ['5', 1000000.0, 1000000.0, 308.29, 308.61, '0', '0']
            ], False)),
            call((1615906730329000, 'USDILS', [
                ['0', 1000000.0, 1000000.0, 3.2997, 3.3016, '0', '0'],
                ['1', 2000000.0, 2000000.0, 3.2996, 3.3017, '0', '0'],
                ['2', 1000000.0, 3000000.0, 3.2995, 3.3018, '0', '0'],
                ['3', 3000000.0, 4000000.0, 3.2994, 3.3019, '0', '0'],
                ['4', 4000000.0, 5000000.0, 3.2993, 3.302, '0', '0'],
                ['5', 5000000.0, 1000000.0, 3.2992, 3.3021, '1', '1']
            ], False)),
            call((1615906730329000, 'USDJPY', [
                ['0', 4000000.0, 4000000.0, 108.899, 108.901, '2', '2'],
                ['1', 3000000.0, 1000000.0, 108.898, 108.901, '1', '1'],
                ['2', 1000000.0, 3000000.0, 108.898, 108.902, '1', '1'],
                ['3', 5000000.0, 5000000.0, 108.897, 108.903, '1', '1'],
                ['4', 5000000.0, 5000000.0, 108.896, 108.903, '2', '2'],
                ['5', 1000000.0, 10000000.0, 108.896, 108.904, '1', '1']
            ], False)),
            call((1615906730329000, 'USDMXN', [
                ['0', 1000000.0, 300000.0, 20.5538, 20.55849, '2', '2'],
                ['1', 1000000.0, 750000.0, 20.5535, 20.55857, '2', '2'],
                ['2', 300000.0, 1500000.0, 20.55349, 20.5588, '2', '2'],
                ['3', 750000.0, 2250000.0, 20.55343, 20.55902, '2', '2'],
                ['4', 1500000.0, 3000000.0, 20.55326, 20.55921, '2', '2'],
                ['5', 2000000.0, 1000000.0, 20.5532, 20.5593, '1', '1']
            ], False)),
            call((1615906730329000, 'USDNOK', [
                ['0', 1000000.0, 1000000.0, 8.47478, 8.47578, '2', '2'],
                ['1', 1600000.0, 1500000.0, 8.4745, 8.47606, '2', '2'],
                ['2', 2000000.0, 2100000.0, 8.47441, 8.47633, '2', '2'],
                ['3', 2600000.0, 4100000.0, 8.47429, 8.47668, '2', '2'],
                ['4', 2900000.0, 4600000.0, 8.47424, 8.47672, '2', '2'],
                ['5', 2000000.0, 1000000.0, 8.4736, 8.477, '0', '0']
            ], False)),
            call((1615906730329000, 'USDPLN', [
                ['0', 600000.0, 600000.0, 3.8563, 3.8568, '2', '2'],
                ['1', 1200000.0, 1100000.0, 3.85619, 3.85689, '2', '2'],
                ['2', 1700000.0, 1700000.0, 3.85615, 3.85693, '2', '2'],
                ['3', 3700000.0, 2300000.0, 3.85608, 3.85698, '2', '2'],
                ['4', 4300000.0, 2900000.0, 3.85607, 3.85702, '2', '2'],
                ['5', 1000000.0, 1000000.0, 3.8559, 3.8575, '0', '0']
            ], False)),
            call((1615906730329000, 'USDRUB', [
                ['0', 1000000.0, 1000000.0, 72.689, 72.7084, '1', '1'],
                ['1', 1000000.0, 3000000.0, 72.6848, 72.7119, '1', '1'],
                ['2', 3000000.0, 1000000.0, 72.6813, 72.715, '2', '2'],
                ['3', 5000000.0, 5000000.0, 72.6712, 72.719, '1', '1'],
                ['4', 6000000.0, 6000000.0, 72.6672, 72.7229, '1', '1']
            ], False)),
            call((1615906730329000, 'USDSEK', [
                ['0', 1000000.0, 1000000.0, 8.522, 8.5232, '2', '2'],
                ['1', 3000000.0, 1500000.0, 8.5218, 8.52335, '2', '2'],
                ['2', 1000000.0, 1600000.0, 8.5217, 8.52337, '2', '2'],
                ['3', 1600000.0, 2100000.0, 8.52158, 8.52345, '2', '2'],
                ['4', 2600000.0, 1000000.0, 8.5215, 8.5235, '1', '1'],
                ['5', 3100000.0, 4600000.0, 8.52147, 8.52367, '2', '2']
            ], False))
        ]
        self.pricefeed.queue.put.assert_has_calls(calls)

    def test_on_mass_quote_missing_subscription(self):
        with patch('app.pricefeed.PriceFeed.send_ack') as send_ack:
            self.pricefeed.on_mass_quote(self.fix_mass_quote_no_id, None)
            self.pricefeed.queue.put.assert_not_called()
            send_ack.assert_not_called()

# on_market_data_snapshot
    def test_market_data_snapshot(self):
        self.pricefeed.active_subscriptions["0"] = "EURUSD"
        self.pricefeed.on_market_data_snapshot(self.fix_market_data_snapshot, None)
        self.pricefeed.queue.put.assert_called_once()
        self.pricefeed.queue.put.assert_called_with((1591185600106000, 'EURUSD', [['0', 1000000.0, 1000000.0, 1.11941, 1.11944, '1', '1']], True))
    def test_market_data_snapshot_zero_qty(self):
        self.pricefeed.active_subscriptions["0"] = "XAUUSD"
        self.pricefeed.on_market_data_snapshot(self.fix_market_data_snapshot_zero_qty, None)
        self.pricefeed.queue.put.assert_called_once()
        self.pricefeed.queue.put.assert_called_with((1616101216225000, 'XAUUSD', [['0', 0.0, 0.0, 1735.98, 1737.04, '2', '2']], True))
    def test_process_market_data_snapshot_gbpusd(self):
        self.pricefeed.active_subscriptions["0"] = "GBPUSD"
        self.pricefeed.on_market_data_snapshot(self.fix_market_data_snapshot_gbpusd, None)
        self.pricefeed.queue.put.assert_called_once()
        quotes = [
            ['1', 1000000.0, 4000000.0, 1.37652, 1.37651, '1', '2'],
            ['2', 3000000.0, 1000000.0, 1.37651, 1.37658, '1', '1'],
            ['0', 5000000.0, 1000000.0, 1.37649, 1.37655, '1', '0']]
        self.pricefeed.queue.put.assert_called_with((1616524203059000, 'GBPUSD', quotes, True))
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

class TestPriceFeedFunctions(unittest.TestCase):

    def test_create_market_data_request(self):
        mdr = pf.create_market_data_request("1", "EUR/USD")
        self.assertEqual("1", mdr.getField(262))        # MDReqID
        self.assertEqual("1", mdr.getField(263))        # SubscriptionRequestType
        self.assertEqual("0", mdr.getField(264))        # MarketDepth
        self.assertEqual("1", mdr.getField(146))        # NoRelatedSym
        group = fix44.MarketDataRequest.NoRelatedSym()
        mdr.getGroup(1, group)
        self.assertEqual("EUR/USD", group.getField(55)) # Symbol

    def test_process_quote_set_bid(self):
        quote_set = pxm44.MassQuote.NoQuoteSets()
        quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
        quote_entry.setField(fix.QuoteEntryID('QuoteEntryID'))
        quote_entry.setField(fix.Issuer('issuer'))
        quote_entry.setField(fix.BidSize(100.0))
        quote_entry.setField(fix.BidSpotRate(1.23))
        quote_set.addGroup(quote_entry)
        res = pf.process_quote_set(quote_set, pxm44.MassQuote.NoQuoteSets.NoQuoteEntries())
        self.assertEqual([['QuoteEntryID', 100.0, None, 1.23, None, 'issuer', None]], res)

    def test_process_quote_set_ask(self):
        quote_set = pxm44.MassQuote.NoQuoteSets()
        quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
        quote_entry.setField(fix.QuoteEntryID('QuoteEntryID'))
        quote_entry.setField(fix.Issuer('issuer'))
        quote_entry.setField(fix.OfferSize(200.0))
        quote_entry.setField(fix.OfferSpotRate(2.34))
        quote_set.addGroup(quote_entry)
        res = pf.process_quote_set(quote_set, pxm44.MassQuote.NoQuoteSets.NoQuoteEntries())
        self.assertEqual([['QuoteEntryID', None, 200.0, None, 2.34, None, 'issuer']], res)

    def test_process_quote_set_bid_ask(self):
        quote_set = pxm44.MassQuote.NoQuoteSets()
        quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
        quote_entry.setField(fix.QuoteEntryID('QuoteEntryID'))
        quote_entry.setField(fix.Issuer('issuer'))
        quote_entry.setField(fix.BidSize(100.0))
        quote_entry.setField(fix.OfferSize(200.0))
        quote_entry.setField(fix.BidSpotRate(1.23))
        quote_entry.setField(fix.OfferSpotRate(2.34))
        quote_set.addGroup(quote_entry)
        res = pf.process_quote_set(quote_set, pxm44.MassQuote.NoQuoteSets.NoQuoteEntries())
        self.assertEqual([['QuoteEntryID', 100.0, 200.0, 1.23, 2.34, 'issuer', 'issuer']], res)

    def test_process_quote_set_bid_ask_no_provider(self):
        quote_set = pxm44.MassQuote.NoQuoteSets()
        quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
        quote_entry.setField(fix.QuoteEntryID('QuoteEntryID'))
        quote_entry.setField(fix.BidSize(100.0))
        quote_entry.setField(fix.OfferSize(200.0))
        quote_entry.setField(fix.BidSpotRate(1.23))
        quote_entry.setField(fix.OfferSpotRate(2.34))
        quote_set.addGroup(quote_entry)
        res = pf.process_quote_set(quote_set, pxm44.MassQuote.NoQuoteSets.NoQuoteEntries())
        self.assertEqual([['QuoteEntryID', 100.0, 200.0, 1.23, 2.34, None, None]], res)
