import unittest

import quickfix as fix

from app.pxm44 import MassQuote, MarketDataSnapshotFullRefresh

class TestMassQuoteClass(unittest.TestCase):

    def setUp(self):
        self.fix_string = "8=FIX.4.4|9=245|35=i|34=2|49=XCxxx|52=20151109-20:20:33.240|56=Q01|117=1|296=1|302=3|295=4|299=0|106=1|134=1000000|135=1000000|188=1.51218|190=1.51223|299=1|134=500000|135=50000|188=1.51218|190=1.51223|299=2|135=500000|190=1.51225|299=3|135=2000000|190=1.51226|10=251|".replace("|", "\x01")
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL("spec/pxm44.xml")

    def test_mass_quote(self):
        mass_quote = MassQuote(self.fix_string, self.data_dictionary)
        self.assertEqual(None, self.data_dictionary.validate(mass_quote))

    def test_no_quote_sets(self):
        mass_quote = MassQuote(self.fix_string, self.data_dictionary)
        self.assertEqual('1', mass_quote.getField(fix.NoQuoteSets().getTag()))
        self.assertEqual(1, mass_quote.groupCount(fix.NoQuoteSets().getTag()))
        quote_set = MassQuote.NoQuoteSets()
        mass_quote.getGroup(1, quote_set)
        self.assertEqual('4', quote_set.getField(fix.NoQuoteEntries().getTag()))
        self.assertEqual(4, quote_set.groupCount(fix.NoQuoteEntries().getTag()))

    def test_no_quote_entries(self):
        mass_quote = MassQuote(self.fix_string, self.data_dictionary)
        quote_set = MassQuote.NoQuoteSets()
        quote_entry = MassQuote.NoQuoteSets.NoQuoteEntries()
        mass_quote.getGroup(1, quote_set)
        quote_set.getGroup(1, quote_entry)
        self.assertEqual('0', quote_entry.getField(299))
        self.assertEqual('1', quote_entry.getField(106))
        self.assertEqual('1000000', quote_entry.getField(134))
        self.assertEqual('1000000', quote_entry.getField(135))
        self.assertEqual('1.51218', quote_entry.getField(188))
        self.assertEqual('1.51223', quote_entry.getField(190))


class TestMarketDataSnapshotClass(unittest.TestCase):

    def setUp(self):
        self.fix_string = "8=FIX.4.4|9=177|35=W|34=136232|49=XCT1|52=20200603-12:00:00.106|56=Q004|55=EUR/USD|262=10|7533=stream1|268=2|269=0|270=1.11941|271=1000000|299=0|106=7|269=1|270=1.11944|271=1000000|299=0|106=7|10=255|".replace("|", "\x01")
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL("spec/pxm44.xml")

    def test_market_data_snapshot(self):
        snapshot = MarketDataSnapshotFullRefresh(self.fix_string, self.data_dictionary)
        self.assertEqual(None, self.data_dictionary.validate(snapshot))

    def test_no_md_entries(self):
        snapshot = MarketDataSnapshotFullRefresh(self.fix_string, self.data_dictionary)
        self.assertEqual('2', snapshot.getField(fix.NoMDEntries().getTag()))
        self.assertEqual(2, snapshot.groupCount(fix.NoMDEntries().getTag()))
        md_entry = MarketDataSnapshotFullRefresh.NoMDEntries()
        snapshot.getGroup(1, md_entry)
        self.assertEqual('0', md_entry.getField(269))
        self.assertEqual('1.11941', md_entry.getField(270))
        self.assertEqual('1000000', md_entry.getField(271))
        self.assertEqual('0', md_entry.getField(299))
        self.assertEqual('7', md_entry.getField(106))
