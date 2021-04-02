import unittest

import quickfix as fix
import quickfix44 as fix44

import app.pricefeed as pf
import app.pxm44 as pxm44

class TestPriceFeedFunctions(unittest.TestCase):
    def setUp(self):
        self.quote_set = pxm44.MassQuote.NoQuoteSets()
        self.quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
        self.md_entry = pxm44.MarketDataSnapshotFullRefresh.NoMDEntries()
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL("spec/pxm44.xml")
        # incremental
        self.fix_mass_quote = fix.Message("8=FIX.4.4|9=135|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|117=1|296=1|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|10=235|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_no_id = fix.Message("8=FIX.4.4|9=129|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|296=1|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|10=230|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_quotesets = fix.Message("8=FIX.4.4|9=201|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|296=2|302=0|295=1|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|302=1|295=1|299=0|106=2|134=2000000|135=2000000|188=2.51218|190=2.51223|10=208|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_large = fix.Message("8=FIX.4.4|9=3325|35=i|34=11|49=XC461|52=20210316-14:58:50.329|56=Q003|296=9|302=37|295=6|299=0|106=0|134=1000000|135=1000000|188=7.76648|190=7.76668|299=1|106=0|134=3000000|135=3000000|188=7.76645|190=7.7667|299=2|106=0|134=5000000|135=5000000|188=7.76643|190=7.76673|299=3|106=0|134=10000000|135=10000000|188=7.76637|190=7.7668|299=4|106=2|134=8000000|135=8000000|188=7.76633|190=7.76683|299=5|106=0|134=25000000|135=25000000|188=7.76618|190=7.767|302=38|295=6|299=0|106=2|134=2800000|135=3600000|188=308.355|190=308.555|299=1|106=2|134=3100000|135=3800000|188=308.354|190=308.556|299=2|106=2|134=3300000|135=3900000|188=308.353|190=308.557|299=3|106=2|134=3600000|135=4100000|188=308.352|190=308.558|299=4|106=2|134=3900000|135=6100000|188=308.351|190=308.559|299=5|106=0|134=1000000|135=1000000|188=308.29|190=308.61|302=39|295=6|299=0|106=0|134=1000000|135=1000000|188=3.2997|190=3.3016|299=1|106=0|134=2000000|135=2000000|188=3.2996|190=3.3017|299=2|106=0|134=1000000|135=3000000|188=3.2995|190=3.3018|299=3|106=0|134=3000000|135=4000000|188=3.2994|190=3.3019|299=4|106=0|134=4000000|135=5000000|188=3.2993|190=3.302|299=5|106=1|134=5000000|135=1000000|188=3.2992|190=3.3021|302=40|295=6|299=0|106=2|134=4000000|135=4000000|188=108.899|190=108.901|299=1|106=1|134=3000000|135=1000000|188=108.898|190=108.901|299=2|106=1|134=1000000|135=3000000|188=108.898|190=108.902|299=3|106=1|134=5000000|135=5000000|188=108.897|190=108.903|299=4|106=2|134=5000000|135=5000000|188=108.896|190=108.903|299=5|106=1|134=1000000|135=10000000|188=108.896|190=108.904|302=41|295=6|299=0|106=2|134=1000000|135=300000|188=20.5538|190=20.55849|299=1|106=2|134=1000000|135=750000|188=20.5535|190=20.55857|299=2|106=2|134=300000|135=1500000|188=20.55349|190=20.5588|299=3|106=2|134=750000|135=2250000|188=20.55343|190=20.55902|299=4|106=2|134=1500000|135=3000000|188=20.55326|190=20.55921|299=5|106=1|134=2000000|135=1000000|188=20.5532|190=20.5593|302=42|295=6|299=0|106=2|134=1000000|135=1000000|188=8.47478|190=8.47578|299=1|106=2|134=1600000|135=1500000|188=8.4745|190=8.47606|299=2|106=2|134=2000000|135=2100000|188=8.47441|190=8.47633|299=3|106=2|134=2600000|135=4100000|188=8.47429|190=8.47668|299=4|106=2|134=2900000|135=4600000|188=8.47424|190=8.47672|299=5|106=0|134=2000000|135=1000000|188=8.4736|190=8.477|302=43|295=6|299=0|106=2|134=600000|135=600000|188=3.8563|190=3.8568|299=1|106=2|134=1200000|135=1100000|188=3.85619|190=3.85689|299=2|106=2|134=1700000|135=1700000|188=3.85615|190=3.85693|299=3|106=2|134=3700000|135=2300000|188=3.85608|190=3.85698|299=4|106=2|134=4300000|135=2900000|188=3.85607|190=3.85702|299=5|106=0|134=1000000|135=1000000|188=3.8559|190=3.8575|302=45|295=5|299=0|106=1|134=1000000|135=1000000|188=72.689|190=72.7084|299=1|106=1|134=1000000|135=3000000|188=72.6848|190=72.7119|299=2|106=2|134=3000000|135=1000000|188=72.6813|190=72.715|299=3|106=1|134=5000000|135=5000000|188=72.6712|190=72.719|299=4|106=1|134=6000000|135=6000000|188=72.6672|190=72.7229|302=46|295=6|299=0|106=2|134=1000000|135=1000000|188=8.522|190=8.5232|299=1|106=2|134=3000000|135=1500000|188=8.5218|190=8.52335|299=2|106=2|134=1000000|135=1600000|188=8.5217|190=8.52337|299=3|106=2|134=1600000|135=2100000|188=8.52158|190=8.52345|299=4|106=1|134=2600000|135=1000000|188=8.5215|190=8.5235|299=5|106=2|134=3100000|135=4600000|188=8.52147|190=8.52367|10=166|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_bid_ask_provider = fix.Message("8=FIX.4.4|9=279|35=i|34=9805389|49=XC461|52=20210504-19:35:05.295|56=Q000|296=1|302=d|295=7|299=8|106=1|188=1.20133|190=1.20133|299=0|106=2|188=1.20128|190=1.20135|299=2|106=1|188=1.20128|299=5|106=1|188=1.20127|190=1.20131|299=1|106=1|188=1.20126|299=9|106=1|190=1.2013|299=7|106=1|190=1.20132|10=173|".replace("|", "\x01"), self.data_dictionary)
        self.fix_mass_quote_offline = fix.Message("8=FIX.4.4|9=155|35=i|296=2|302=EUR/USD|295=1|299=0|134=1000000|135=1000000|188=1.22015|190=1.22016|302=USD/CAD|295=1|299=0|134=1000000|135=1000000|188=1.21100|190=1.21105|10=143|".replace("|", "\x01"), self.data_dictionary)
        # snapshots
        self.fix_market_data_snapshot = fix.Message("8=FIX.4.4|9=163|35=W|34=136232|49=XCT1|52=20200603-12:00:00.106|56=Q004|55=EUR/USD|262=0|268=2|269=0|270=1.11941|271=1000000|299=0|106=1|269=1|270=1.11944|271=1000000|299=0|106=1|10=240|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_snapshot_zero_qty = fix.Message("8=FIX.4.4|9=153|35=W|34=848278|49=XC461|52=20210318-21:00:16.225|56=Q003|55=XAU/USD|262=51|268=2|269=0|270=1735.98|271=0|299=0|106=2|269=1|270=1737.04|271=0|299=0|106=2|10=047|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_snapshot_gbpusd = fix.Message("8=FIX.4.4|9=333|35=W|34=118004|49=XC461|52=20210323-18:30:03.059|56=Q003|55=GBP/USD|262=27|268=6|269=0|270=1.37652|271=1000000|299=1|106=1|269=0|270=1.37651|271=3000000|299=2|106=1|269=0|270=1.37649|271=5000000|299=0|106=1|269=1|270=1.37651|271=4000000|299=1|106=2|269=1|270=1.37655|271=1000000|299=0|106=0|269=1|270=1.37658|271=1000000|299=2|106=1|10=155|".replace("|", "\x01"), self.data_dictionary)
        self.fix_market_data_snapshot_offline = fix.Message("8=FIX.4.4|9=104|35=W|55=AUD/CAD|262=AUD/CAD|268=2|269=0|270=1.12885|271=200000|299=0|269=1|270=1.12887|271=200000|299=0|10=017|".replace("|", "\x01"), self.data_dictionary)

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

    def test_process_mass_quote_with_quote_id(self):
        subs = { '0': 'EURUSD'}
        quotes = [['0', 1000000.0, 1000000.0, 1.51218, 1.51223, '1', '1']]
        res = pf.process_mass_quote(self.fix_mass_quote, subs)
        self.assertEqual([(1447100433240000, 'EURUSD', quotes, False)], res)

    def test_process_mass_quote_missing_subscription(self):
        res = pf.process_mass_quote(self.fix_mass_quote_no_id, {})
        self.assertEqual([], res)

    def test_process_mass_quote_multiple_quotesets(self):
        subs = { '0': 'EURUSD', '1': 'AUDCAD'}
        expected = [
            (1447100433240000, 'EURUSD', [['0', 1000000.0, 1000000.0, 1.51218, 1.51223, '1', '1']], False),
            (1447100433240000, 'AUDCAD', [['0', 2000000.0, 2000000.0, 2.51218, 2.51223, '2', '2']], False)
        ]
        res = pf.process_mass_quote(self.fix_mass_quote_quotesets, subs)
        self.assertEqual(res, expected)

    def test_process_mass_quote_large_quotesets(self):
        subs = {
            '37':"USDHKD",
            '38':"USDHUF",
            '39':"USDILS",
            '40':"USDJPY",
            '41':"USDMXN",
            '42':"USDNOK",
            '43':"USDPLN",
            '45':"USDRUB",
            '46':"USDSEK"
        }
        quotes = [
            (1615906730329000, 'USDHKD', [
                ['0', 1000000.0, 1000000.0, 7.76648, 7.76668, '0', '0'],
                ['1', 3000000.0, 3000000.0, 7.76645, 7.7667, '0', '0'],
                ['2', 5000000.0, 5000000.0, 7.76643, 7.76673, '0', '0'],
                ['3', 10000000.0, 10000000.0, 7.76637, 7.7668, '0', '0'],
                ['4', 8000000.0, 8000000.0, 7.76633, 7.76683, '2', '2'],
                ['5', 25000000.0, 25000000.0, 7.76618, 7.767, '0', '0']
            ], False),
            (1615906730329000, 'USDHUF', [
                ['0', 2800000.0, 3600000.0, 308.355, 308.555, '2', '2'],
                ['1', 3100000.0, 3800000.0, 308.354, 308.556, '2', '2'],
                ['2', 3300000.0, 3900000.0, 308.353, 308.557, '2', '2'],
                ['3', 3600000.0, 4100000.0, 308.352, 308.558, '2', '2'],
                ['4', 3900000.0, 6100000.0, 308.351, 308.559, '2', '2'],
                ['5', 1000000.0, 1000000.0, 308.29, 308.61, '0', '0']
            ], False),
            (1615906730329000, 'USDILS', [
                ['0', 1000000.0, 1000000.0, 3.2997, 3.3016, '0', '0'],
                ['1', 2000000.0, 2000000.0, 3.2996, 3.3017, '0', '0'],
                ['2', 1000000.0, 3000000.0, 3.2995, 3.3018, '0', '0'],
                ['3', 3000000.0, 4000000.0, 3.2994, 3.3019, '0', '0'],
                ['4', 4000000.0, 5000000.0, 3.2993, 3.302, '0', '0'],
                ['5', 5000000.0, 1000000.0, 3.2992, 3.3021, '1', '1']
            ], False),
            (1615906730329000, 'USDJPY', [
                ['0', 4000000.0, 4000000.0, 108.899, 108.901, '2', '2'],
                ['1', 3000000.0, 1000000.0, 108.898, 108.901, '1', '1'],
                ['2', 1000000.0, 3000000.0, 108.898, 108.902, '1', '1'],
                ['3', 5000000.0, 5000000.0, 108.897, 108.903, '1', '1'],
                ['4', 5000000.0, 5000000.0, 108.896, 108.903, '2', '2'],
                ['5', 1000000.0, 10000000.0, 108.896, 108.904, '1', '1']
            ], False),
            (1615906730329000, 'USDMXN', [
                ['0', 1000000.0, 300000.0, 20.5538, 20.55849, '2', '2'],
                ['1', 1000000.0, 750000.0, 20.5535, 20.55857, '2', '2'],
                ['2', 300000.0, 1500000.0, 20.55349, 20.5588, '2', '2'],
                ['3', 750000.0, 2250000.0, 20.55343, 20.55902, '2', '2'],
                ['4', 1500000.0, 3000000.0, 20.55326, 20.55921, '2', '2'],
                ['5', 2000000.0, 1000000.0, 20.5532, 20.5593, '1', '1']
            ], False),
            (1615906730329000, 'USDNOK', [
                ['0', 1000000.0, 1000000.0, 8.47478, 8.47578, '2', '2'],
                ['1', 1600000.0, 1500000.0, 8.4745, 8.47606, '2', '2'],
                ['2', 2000000.0, 2100000.0, 8.47441, 8.47633, '2', '2'],
                ['3', 2600000.0, 4100000.0, 8.47429, 8.47668, '2', '2'],
                ['4', 2900000.0, 4600000.0, 8.47424, 8.47672, '2', '2'],
                ['5', 2000000.0, 1000000.0, 8.4736, 8.477, '0', '0']
            ], False),
            (1615906730329000, 'USDPLN', [
                ['0', 600000.0, 600000.0, 3.8563, 3.8568, '2', '2'],
                ['1', 1200000.0, 1100000.0, 3.85619, 3.85689, '2', '2'],
                ['2', 1700000.0, 1700000.0, 3.85615, 3.85693, '2', '2'],
                ['3', 3700000.0, 2300000.0, 3.85608, 3.85698, '2', '2'],
                ['4', 4300000.0, 2900000.0, 3.85607, 3.85702, '2', '2'],
                ['5', 1000000.0, 1000000.0, 3.8559, 3.8575, '0', '0']
            ], False),
            (1615906730329000, 'USDRUB', [
                ['0', 1000000.0, 1000000.0, 72.689, 72.7084, '1', '1'],
                ['1', 1000000.0, 3000000.0, 72.6848, 72.7119, '1', '1'],
                ['2', 3000000.0, 1000000.0, 72.6813, 72.715, '2', '2'],
                ['3', 5000000.0, 5000000.0, 72.6712, 72.719, '1', '1'],
                ['4', 6000000.0, 6000000.0, 72.6672, 72.7229, '1', '1']
            ], False),
            (1615906730329000, 'USDSEK', [
                ['0', 1000000.0, 1000000.0, 8.522, 8.5232, '2', '2'],
                ['1', 3000000.0, 1500000.0, 8.5218, 8.52335, '2', '2'],
                ['2', 1000000.0, 1600000.0, 8.5217, 8.52337, '2', '2'],
                ['3', 1600000.0, 2100000.0, 8.52158, 8.52345, '2', '2'],
                ['4', 2600000.0, 1000000.0, 8.5215, 8.5235, '1', '1'],
                ['5', 3100000.0, 4600000.0, 8.52147, 8.52367, '2', '2']
            ], False)
        ]
        res = pf.process_mass_quote(self.fix_mass_quote_large, subs)
        self.assertEqual(9, len(res))
        self.assertEqual(quotes[0], res[0])
        self.assertEqual(quotes[1], res[1])
        self.assertEqual(quotes[2], res[2])
        self.assertEqual(quotes[3], res[3])
        self.assertEqual(quotes[4], res[4])
        self.assertEqual(quotes[5], res[5])
        self.assertEqual(quotes[6], res[6])
        self.assertEqual(quotes[7], res[7])
        self.assertEqual(quotes[8], res[8])

    def test_process_mass_quote_offline(self):
        expected = [
            (12345, 'EURUSD', [['0', 1000000.0, 1000000.0, 1.22015, 1.22016, None, None]], False),
            (12345, 'USDCAD', [['0', 1000000.0, 1000000.0, 1.21100, 1.21105, None, None]], False)
        ]
        res = pf.process_mass_quote(self.fix_mass_quote_offline, None, message_time=12345, offline=True)
        self.assertEqual(res, expected)

    def test_process_mass_quote_offline_hardcoded_provider(self):
        expected = [
            (12345, 'EURUSD', [['0', 1000000.0, 1000000.0, 1.22015, 1.22016, '1', '1']], False),
            (12345, 'USDCAD', [['0', 1000000.0, 1000000.0, 1.21100, 1.21105, '1', '1']], False)
        ]
        res = pf.process_mass_quote(self.fix_mass_quote_offline, None, message_time=12345, offline=True, hardcoded_provider='1')
        self.assertEqual(res, expected)

    def test_process_market_data_snapshot(self):
        quotes = [['0', 1000000.0, 1000000.0, 1.11941, 1.11944, '1', '1']]
        res = pf.process_market_data_snapshot(self.fix_market_data_snapshot)
        self.assertEqual((1591185600106000, 'EURUSD', quotes, True), res)

    def test_process_market_data_snapshot_zero_qty(self):
        quotes = [['0', 0.0, 0.0, 1735.98, 1737.04, '2', '2']]
        res = pf.process_market_data_snapshot(self.fix_market_data_snapshot_zero_qty)
        self.assertEqual((1616101216225000, 'XAUUSD', quotes, True), res)

    def test_process_market_data_snapshot_gbpusd(self):
        quotes = [
            ['1', 1000000.0, 4000000.0, 1.37652, 1.37651, '1', '2'],
            ['2', 3000000.0, 1000000.0, 1.37651, 1.37658, '1', '1'],
            ['0', 5000000.0, 1000000.0, 1.37649, 1.37655, '1', '0']]
        res = pf.process_market_data_snapshot(self.fix_market_data_snapshot_gbpusd)
        self.assertEqual((1616524203059000, 'GBPUSD', quotes, True), res)

    def test_process_market_data_snapshot_offline(self):
        quotes = [['0', 200000.0, 200000.0, 1.12885, 1.12887, None, None]]
        res = pf.process_market_data_snapshot(self.fix_market_data_snapshot_offline)
        self.assertEqual((0, 'AUDCAD', quotes, True), res)

    def test_process_market_data_snapshot_offline_hardcoded_provider(self):
        quotes = [['0', 200000.0, 200000.0, 1.12885, 1.12887, '1', '1']]
        res = pf.process_market_data_snapshot(self.fix_market_data_snapshot_offline, hardcoded_provider='1')
        self.assertEqual((0, 'AUDCAD', quotes, True), res)

    def test_clear_book(self):
        res = pf.clear_book('EURUSD')
        self.assertEqual((-1, 'EURUSD', [], True), res)

    def test_bid_and_ask_provider(self):
        quotes = [
            ['8', None, None, 1.20133, 1.20133, None, '1'],
            ['0', None, None, 1.20128, 1.20135, None, '2'],
            ['2', None, None, 1.20128, None,    '1', None],
            ['5', None, None, 1.20127, 1.20131, None, '1'],
            ['1', None, None, 1.20126, None,    '1', None],
            ['9', None, None, None,    1.2013,  None, '1'],
            ['7', None, None, None,    1.20132, None, '1']
        ]
        res = pf.process_mass_quote(self.fix_mass_quote_bid_ask_provider, {'d' : 'EURUSD'})
        self.assertEqual([(1620156905295000, 'EURUSD', quotes, False)], res)

    def test_log_time_to_timestamp(self):
        res = pf.log_time_to_timestamp('2021-05-20 13:00:00.453')
        self.assertEqual(1621515600453000, res)
