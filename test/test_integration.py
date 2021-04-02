import unittest
from unittest.mock import Mock, patch, call

from multiprocessing import Queue
import numpy as np

import quickfix as fix
import quickfix44 as fix44

import app.bookbuilder as bb
import app.fixpricefeed as pf
import app.pxm44 as pxm44

class TestIntegrationClass(unittest.TestCase):
    def setUp(self):
        self.pricefeed_queue = Queue()
        self.filewriter_queue = Queue()
        self.shutdown_event = Mock()
        self.shutdown_consumer = Mock()
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL('spec/pxm44.xml')
        self.pricefeed = pf.FixPriceFeed(self.pricefeed_queue, self.shutdown_event, ['EUR/USD', 'USD/CAD'])
        self.bookbuilder = bb.BookBuilder(self.pricefeed_queue, self.filewriter_queue,
                                          self.shutdown_event, self.shutdown_consumer,
                                          None, max_levels=3)

# 1.) logon

    def test_logon(self):
        msg = fix.Message('8=FIX.4.4|9=106|35=A|34=1|49=Q000|52=20210328-06:44:27.779|56=XC461|553=primexm_TradeFeedr_q|554=******|98=0|108=30|141=Y|10=59|'.replace('|', '\x01'), self.data_dictionary)
        # nothing to do here (callback for offline?)

# 2.) v x 2 crosses

    def test_subscribe(self):
        sub1 = fix.Message('8=FIX.4.4|9=112|35=V|34=2|49=Q000|52=20210328-21:00:00.516|56=XC461|262=0|263=1|264=16|265=1|146=1|55=EUR/USD|267=2|269=0|269=1|10=117|'.replace('|', '\x01'), self.data_dictionary)
        sub2 = fix.Message('8=FIX.4.4|9=112|35=V|34=3|49=Q000|52=20210328-21:00:00.516|56=XC461|262=1|263=1|264=16|265=1|146=1|55=USD/CAD|267=2|269=0|269=1|10=83|'.replace('|', '\x01'), self.data_dictionary)
        # nothing to do here (callback for offline?)

# 3.) w x 2 crosses

    # EUR/USD
    #                   bids | asks
    # [0] 1000000 @ 2.49 lp0 | [0] 1000000 @ 2.50 lp0
    # [1] 2000000 @ 2.48 lp0 | [1] 2000000 @ 2.51 lp0
    def test_snapshot_empty_book_1(self):
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=4|49=XC461|52=20210328-21:00:17.156|56=Q000|55=EUR/USD|262=0|268=4|269=1|270=2.50|271=1000000|299=0|106=0|269=1|270=2.51|271=2000000|299=1|106=0|269=0|270=2.49|271=1000000|299=0|106=0|269=0|270=2.48|271=2000000|299=1|106=0|10=199|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217156000, 'EURUSD', [
            ['0', 1000000.0, 1000000.0, 2.49, 2.50, '0', '0'],
            ['1', 2000000.0, 2000000.0, 2.48, 2.51, '0', '0'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217156000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217156000, book['time'])
        self.assertEqual(1616965217156000, book['bid_time0'])
        self.assertEqual(2.49, book['bid_px0'])
        self.assertEqual(1000000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217156000, book['bid_time1'])
        self.assertEqual(2.48, book['bid_px1'])
        self.assertEqual(2000000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # asks
        self.assertEqual(1616965217156000, book['ask_time0'])
        self.assertEqual(2.50, book['ask_px0'])
        self.assertEqual(1000000, book['ask_size0'])
        self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(1616965217156000, book['ask_time1'])
        self.assertEqual(2.51, book['ask_px1'])
        self.assertEqual(2000000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_eurusd_0001.csv', book, delimiter=',', fmt='%s')

    # USD/CAD
    #                   bids | asks
    # [0] 1000000 @ 1.49 lp0 | [0] 1000000 @ 1.50 lp1
    # [1] 2000000 @ 1.48 lp1 | [1] 2000000 @ 1.51 lp0
    def test_snapshot_empty_book_2(self):
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=5|49=XC461|52=20210328-21:00:17.156|56=Q000|55=USD/CAD|262=1|268=4|269=1|270=1.51|271=2000000|299=1|106=0|269=0|270=1.48|271=2000000|299=1|106=1|269=1|270=1.50|271=1000000|299=0|106=1|269=0|270=1.49|271=1000000|299=0|106=0|10=163|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217156000, 'USDCAD', [
            ['1', 2000000.0, 2000000.0, 1.48, 1.51, '1', '0'],
            ['0', 1000000.0, 1000000.0, 1.49, 1.50, '0', '1'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217156000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965217156000, book['time'])
        self.assertEqual(1616965217156000, book['bid_time0'])
        self.assertEqual(1.49, book['bid_px0'])
        self.assertEqual(1000000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217156000, book['bid_time1'])
        self.assertEqual(1.48, book['bid_px1'])
        self.assertEqual(2000000, book['bid_size1'])
        self.assertEqual(b'1', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # asks
        self.assertEqual(1616965217156000, book['ask_time0'])
        self.assertEqual(1.50, book['ask_px0'])
        self.assertEqual(1000000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217156000, book['ask_time1'])
        self.assertEqual(1.51, book['ask_px1'])
        self.assertEqual(2000000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_usdcad_0002.csv', book, delimiter=',', fmt='%s')

# 4.) i
#     4 comb below x 2 sides x 2 crosses x 2 levels
#     feed price qty
#     price
#     feed price
#     qty

# update all entries for 1 cross

    # EUR/USD
    #                   bids | asks
    # [0] 1100000*@ 2.47*lp0*| [1] 2200000*@ 2.48*lp1*
    # [1] 1100000*@ 2.46*lp1*| [0] 2200000*@ 2.49*lp0*
    def test_incremental_book_1(self):
        with patch('app.fixpricefeed.FixPriceFeed.send_ack') as send_ack:
            msg = fix.Message('8=FIX.4.4|9=184|35=i|34=6|49=XC461|52=20210328-21:00:17.157|56=Q000|117=1|296=1|302=0|295=2|299=0|106=0|134=1100000|135=2200000|188=2.47|190=2.49|299=1|106=1|134=1100000|135=2200000|188=2.46|190=2.48|10=245|'.replace('|', '\x01'), self.data_dictionary)
            self.pricefeed.active_subscriptions['0'] = 'EURUSD'
            self.pricefeed.on_mass_quote(msg, None)
            item = self.pricefeed.queue.get()
            self.assertEqual((1616965217157000, 'EURUSD', [
                ['0', 1100000.0, 2200000.0, 2.47, 2.49, '0', '0'],
                ['1', 1100000.0, 2200000.0, 2.46, 2.48, '1', '1'],
            ], False), item)
            self.bookbuilder.process_item(item)
            time, symbol, book = self.bookbuilder.outbound_queue.get()
            self.assertEqual(1616965217157000, time)
            self.assertEqual('EURUSD', symbol)
            self.assertEqual(1616965217157000, book['time'])
            self.assertEqual(1616965217157000, book['bid_time0'])
            self.assertEqual(2.47, book['bid_px0'])
            self.assertEqual(1100000, book['bid_size0'])
            self.assertEqual(b'0', book['bid_provider0'][0])
            self.assertEqual(1616965217157000, book['bid_time1'])
            self.assertEqual(2.46, book['bid_px1'])
            self.assertEqual(1100000, book['bid_size1'])
            self.assertEqual(b'1', book['bid_provider1'][0])
            self.assertEqual(0, book['bid_time2'])
            self.assertEqual(0, book['bid_px2'])
            self.assertEqual(0, book['bid_size2'])
            self.assertEqual(b'', book['bid_provider2'][0])
            # asks
            self.assertEqual(1616965217157000, book['ask_time0'])
            self.assertEqual(2.48, book['ask_px0'])
            self.assertEqual(2200000, book['ask_size0'])
            self.assertEqual(b'1', book['ask_provider0'][0])
            self.assertEqual(1616965217157000, book['ask_time1'])
            self.assertEqual(2.49, book['ask_px1'])
            self.assertEqual(2200000, book['ask_size1'])
            self.assertEqual(b'0', book['ask_provider1'][0])
            self.assertEqual(0, book['ask_time2'])
            self.assertEqual(0, book['ask_px2'])
            self.assertEqual(0, book['ask_size2'])
            self.assertEqual(b'', book['ask_provider2'][0])
            np.savetxt('/tmp/book_eurusd_0003.csv', book, delimiter=',', fmt='%s')

# update all entries for 2 crosses

    # EUR/USD
    #                   bids | asks
    # [0] 1200000 @ 2.46 lp1 | [0] 1200000 @ 2.47 lp1
    # [1] 2300000 @ 2.45 lp0 | [1] 2300000 @ 2.48 lp0
    #
    # USD/CAD
    #                   bids | asks
    # [0] 2200000 @ 1.47 lp0 | [0] 1100000 @ 1.49 lp1 *** asks could be either way around
    # [1] 2200000 @ 1.46 lp1 | [1] 1100000 @ 1.49 lp0
    def test_incremental_book_2(self):
        with patch('app.fixpricefeed.FixPriceFeed.send_ack') as send_ack:
            msg = fix.Message('8=FIX.4.4|9=304|35=i|34=6|49=XC461|52=20210328-21:00:17.159|56=Q000|117=1|296=2|302=0|295=2|299=0|106=1|134=1200000|135=1200000|188=2.46|190=2.47|299=1|106=0|134=2300000|135=2300000|188=2.45|190=2.48|302=1|295=2|299=0|106=0|134=2200000|135=1100000|188=1.47|190=1.49|299=1|106=1|134=2200000|135=1100000|188=1.46|190=1.49|10=117|'.replace('|', '\x01'), self.data_dictionary)
            self.pricefeed.active_subscriptions['0'] = 'EURUSD'
            self.pricefeed.active_subscriptions['1'] = 'USDCAD'
            self.pricefeed.on_mass_quote(msg, None)
            item = self.pricefeed.queue.get()
            self.assertEqual((1616965217159000, 'EURUSD', [
                ['0', 1200000.0, 1200000.0, 2.46, 2.47, '1', '1'],
                ['1', 2300000.0, 2300000.0, 2.45, 2.48, '0', '0'],
            ], False), item)
            self.bookbuilder.process_item(item)
            time, symbol, book = self.bookbuilder.outbound_queue.get()
            self.assertEqual(1616965217159000, time)
            self.assertEqual('EURUSD', symbol)
            self.assertEqual(1616965217159000, book['time'])
            self.assertEqual(1616965217159000, book['bid_time0'])
            self.assertEqual(2.46, book['bid_px0'])
            self.assertEqual(1200000, book['bid_size0'])
            self.assertEqual(b'1', book['bid_provider0'][0])
            self.assertEqual(1616965217159000, book['bid_time1'])
            self.assertEqual(2.45, book['bid_px1'])
            self.assertEqual(2300000, book['bid_size1'])
            self.assertEqual(b'0', book['bid_provider1'][0])
            self.assertEqual(0, book['bid_time2'])
            self.assertEqual(0, book['bid_px2'])
            self.assertEqual(0, book['bid_size2'])
            self.assertEqual(b'', book['bid_provider2'][0])
            # asks
            self.assertEqual(1616965217159000, book['ask_time0'])
            self.assertEqual(2.47, book['ask_px0'])
            self.assertEqual(1200000, book['ask_size0'])
            self.assertEqual(b'1', book['ask_provider0'][0])
            self.assertEqual(1616965217159000, book['ask_time1'])
            self.assertEqual(2.48, book['ask_px1'])
            self.assertEqual(2300000, book['ask_size1'])
            self.assertEqual(b'0', book['ask_provider1'][0])
            self.assertEqual(0, book['ask_time2'])
            self.assertEqual(0, book['ask_px2'])
            self.assertEqual(0, book['ask_size2'])
            self.assertEqual(b'', book['ask_provider2'][0])
            np.savetxt('/tmp/book_eurusd_0004.csv', book, delimiter=',', fmt='%s')
            # second quoteset
            item = self.pricefeed.queue.get()
            self.assertEqual((1616965217159000, 'USDCAD', [
                ['0', 2200000.0, 1100000.0, 1.47, 1.49, '0', '0'],
                ['1', 2200000.0, 1100000.0, 1.46, 1.49, '1', '1'],
            ], False), item)
            self.bookbuilder.process_item(item)
            time, symbol, book = self.bookbuilder.outbound_queue.get()
            self.assertEqual(1616965217159000, time)
            self.assertEqual('USDCAD', symbol)
            self.assertEqual(1616965217159000, book['time'])
            self.assertEqual(1616965217159000, book['bid_time0'])
            self.assertEqual(1.47, book['bid_px0'])
            self.assertEqual(2200000, book['bid_size0'])
            self.assertEqual(b'0', book['bid_provider0'][0])
            self.assertEqual(1616965217159000, book['bid_time1'])
            self.assertEqual(1.46, book['bid_px1'])
            self.assertEqual(2200000, book['bid_size1'])
            self.assertEqual(b'1', book['bid_provider1'][0])
            self.assertEqual(0, book['bid_time2'])
            self.assertEqual(0, book['bid_px2'])
            self.assertEqual(0, book['bid_size2'])
            self.assertEqual(b'', book['bid_provider2'][0])
            # asks
            self.assertEqual(1616965217159000, book['ask_time0'])
            self.assertEqual(1.49, book['ask_px0'])
            self.assertEqual(1100000, book['ask_size0'])
            self.assertEqual(b'0', book['ask_provider0'][0])
            self.assertEqual(1616965217159000, book['ask_time1'])
            self.assertEqual(1.49, book['ask_px1'])
            self.assertEqual(1100000, book['ask_size1'])
            self.assertEqual(b'1', book['ask_provider1'][0])
            self.assertEqual(0, book['ask_time2'])
            self.assertEqual(0, book['ask_px2'])
            self.assertEqual(0, book['ask_size2'])
            self.assertEqual(b'', book['ask_provider2'][0])
            np.savetxt('/tmp/book_usdcad_0004.csv', book, delimiter=',', fmt='%s')

# update bid for 1 cross:

## update bid price for 1 cross (id 0)

    # EUR/USD
    #                   bids | asks
    # [1] 2300000 @ 2.45 lp0 | [0] 1200000 @ 2.47 lp1
    # [0] 1200000 @ 2.44*lp1 | [1] 2300000 @ 2.48 lp0
    def test_incremental_book_bid_price(self):
        # hack but we dont want to keep state so...
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.46, 'size': 1200000.0, 'provider': '1', 'time': 1616965217159000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1200000.0, 'provider': '1', 'time': 1616965217159000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2300000.0, 'provider': '0', 'time': 1616965217159000},
            'S1': {'entry_type': 1, 'price': 2.48, 'size': 2300000.0, 'provider': '0', 'time': 1616965217159000}
        }

        msg = fix.Message('8=FIX.4.4|9=91|35=i|34=6|49=XC461|52=20210328-21:00:17.160|56=Q000|296=1|302=0|295=1|299=0|106=1|188=2.44|10=0|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['0'] = 'EURUSD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217160000, 'EURUSD', [
            ['0', None, None, 2.44, None, '1', None]
        ], False), item)
        # only bids updated
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217160000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217160000, book['time'])
        self.assertEqual(1616965217159000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(2300000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217160000, book['bid_time1'])
        self.assertEqual(2.44, book['bid_px1'])
        self.assertEqual(1200000, book['bid_size1'])
        self.assertEqual(b'1', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # no change to asks
        self.assertEqual(1616965217159000, book['ask_time0'])
        self.assertEqual(2.47, book['ask_px0'])
        self.assertEqual(1200000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217159000, book['ask_time1'])
        self.assertEqual(2.48, book['ask_px1'])
        self.assertEqual(2300000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_eurusd_0005.csv', book, delimiter=',', fmt='%s')

## update bid qty for 1 cross (id 1)

    # EUR/USD
    #                   bids | asks
    # [1] 2400000*@ 2.45 lp0 | [0] 1200000 @ 2.47 lp1
    # [0] 1200000 @ 2.44 lp1 | [1] 2300000 @ 2.48 lp0
    def test_incremental_book_bid_qty(self):
        # restore book state
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.44, 'size': 1200000.0, 'provider': '1', 'time': 1616965217160000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1200000.0, 'provider': '1', 'time': 1616965217159000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2300000.0, 'provider': '0', 'time': 1616965217159000},
            'S1': {'entry_type': 1, 'price': 2.48, 'size': 2300000.0, 'provider': '0', 'time': 1616965217159000}
        }
        msg = fix.Message('8=FIX.4.4|9=88|35=i|34=6|49=XC461|52=20210328-21:00:17.161|56=Q000|296=1|302=0|295=1|299=1|134=2400000|10=135|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['0'] = 'EURUSD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217161000, 'EURUSD', [
            ['1', 2400000.0, None, None, None, None, None]
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217161000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217161000, book['time'])
        # only bids updated
        self.assertEqual(1616965217161000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(2400000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217160000, book['bid_time1'])
        self.assertEqual(2.44, book['bid_px1'])
        self.assertEqual(1200000, book['bid_size1'])
        self.assertEqual(b'1', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # no change to asks
        self.assertEqual(1616965217159000, book['ask_time0'])
        self.assertEqual(2.47, book['ask_px0'])
        self.assertEqual(1200000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217159000, book['ask_time1'])
        self.assertEqual(2.48, book['ask_px1'])
        self.assertEqual(2300000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_eurusd_0006.csv', book, delimiter=',', fmt='%s')

## update bid price+provider for 1 cross (id 0)

    # EUR/USD
    #                   bids | asks
    # [1] 2400000 @ 2.45 lp0 | [0] 1200000 @ 2.47 lp1
    # [0] 1200000 @ 2.43*lp0*| [1] 2300000 @ 2.48 lp0
    def test_incremental_book_bid_price_and_provider(self):
        # restore book state
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.44, 'size': 1200000.0, 'provider': '1', 'time': 1616965217160000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1200000.0, 'provider': '1', 'time': 1616965217159000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2400000.0, 'provider': '0', 'time': 1616965217161000},
            'S1': {'entry_type': 1, 'price': 2.48, 'size': 2300000.0, 'provider': '0', 'time': 1616965217159000}
        }
        msg = fix.Message('8=FIX.4.4|9=91|35=i|34=6|49=XC461|52=20210328-21:00:17.162|56=Q000|296=1|302=0|295=1|299=0|106=0|188=2.43|10=0|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['0'] = 'EURUSD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217162000, 'EURUSD', [
            ['0', None, None, 2.43, None, '0', None]
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217162000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217162000, book['time'])
        self.assertEqual(1616965217161000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(2400000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217162000, book['bid_time1'])
        self.assertEqual(2.43, book['bid_px1'])
        self.assertEqual(1200000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # no change to asks
        self.assertEqual(1616965217159000, book['ask_time0'])
        self.assertEqual(2.47, book['ask_px0'])
        self.assertEqual(1200000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217159000, book['ask_time1'])
        self.assertEqual(2.48, book['ask_px1'])
        self.assertEqual(2300000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_eurusd_0007.csv', book, delimiter=',', fmt='%s')


# update ask for 1 cross:

## update ask price for 1 cross (id 1)

    # EUR/USD
    #                   bids | asks
    # [1] 2400000 @ 2.45 lp0 | [0] 1200000 @ 2.47 lp1
    # [0] 1200000 @ 2.43 lp0 | [1] 2300000 @ 2.49*lp0
    def test_incremental_book_ask_price(self):
        # restore book state
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.43, 'size': 1200000.0, 'provider': '0', 'time': 1616965217162000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1200000.0, 'provider': '1', 'time': 1616965217159000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2400000.0, 'provider': '0', 'time': 1616965217161000},
            'S1': {'entry_type': 1, 'price': 2.48, 'size': 2300000.0, 'provider': '0', 'time': 1616965217159000}
        }
        msg = fix.Message('8=FIX.4.4|9=91|35=i|34=6|49=XC461|52=20210328-21:00:17.163|56=Q000|296=1|302=0|295=1|299=1|106=0|190=2.49|10=1|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['0'] = 'EURUSD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217163000, 'EURUSD', [
            ['1', None, None, None, 2.49, None, '0']
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217163000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217163000, book['time'])
        # check asks
        self.assertEqual(1616965217159000, book['ask_time0'])
        self.assertEqual(2.47, book['ask_px0'])
        self.assertEqual(1200000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217163000, book['ask_time1'])
        self.assertEqual(2.49, book['ask_px1'])
        self.assertEqual(2300000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        # no change to bids
        self.assertEqual(1616965217161000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(2400000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217162000, book['bid_time1'])
        self.assertEqual(2.43, book['bid_px1'])
        self.assertEqual(1200000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        np.savetxt('/tmp/book_eurusd_0008.csv', book, delimiter=',', fmt='%s')

## update ask qty for 1 cross (id 0)

    # EUR/USD
    #                   bids | asks
    # [1] 2400000 @ 2.45 lp0 | [0] 1300000*@ 2.47 lp1
    # [0] 1200000 @ 2.43 lp0 | [1] 2300000 @ 2.49 lp0
    def test_incremental_book_ask_qty(self):
        # restore book state
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.43, 'size': 1200000.0, 'provider': '0', 'time': 1616965217162000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1200000.0, 'provider': '1', 'time': 1616965217159000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2400000.0, 'provider': '0', 'time': 1616965217161000},
            'S1': {'entry_type': 1, 'price': 2.49, 'size': 2300000.0, 'provider': '0', 'time': 1616965217163000}
        }
        msg = fix.Message('8=FIX.4.4|9=88|35=i|34=6|49=XC461|52=20210328-21:00:17.164|56=Q000|296=1|302=0|295=1|299=0|135=1300000|10=136|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['0'] = 'EURUSD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217164000, 'EURUSD', [
            ['0', None, 1300000.0, None, None, None, None]
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217164000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217164000, book['time'])
        # check asks
        self.assertEqual(1616965217164000, book['ask_time0'])
        self.assertEqual(2.47, book['ask_px0'])
        self.assertEqual(1300000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217163000, book['ask_time1'])
        self.assertEqual(2.49, book['ask_px1'])
        self.assertEqual(2300000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        # no change to bids
        self.assertEqual(1616965217161000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(2400000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217162000, book['bid_time1'])
        self.assertEqual(2.43, book['bid_px1'])
        self.assertEqual(1200000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        np.savetxt('/tmp/book_eurusd_0009.csv', book, delimiter=',', fmt='%s')

## update ask price+provider for 1 cross (level 1)

    # EUR/USD
    #                   bids | asks
    # [1] 2400000 @ 2.45 lp0 | [1] 2300000 @ 2.46*lp1*
    # [0] 1200000 @ 2.43 lp0 | [0] 1300000 @ 2.47 lp1
    def test_incremental_book_ask_price_and_provider(self):
        # restore book state
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.43, 'size': 1200000.0, 'provider': '0', 'time': 1616965217162000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1300000.0, 'provider': '1', 'time': 1616965217164000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2400000.0, 'provider': '0', 'time': 1616965217161000},
            'S1': {'entry_type': 1, 'price': 2.49, 'size': 2300000.0, 'provider': '0', 'time': 1616965217163000}
        }
        msg = fix.Message('8=FIX.4.4|9=91|35=i|34=6|49=XC461|52=20210328-21:00:17.165|56=Q000|296=1|302=0|295=1|299=1|106=1|190=2.46|10=1|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['0'] = 'EURUSD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217165000, 'EURUSD', [
            ['1', None, None, None, 2.46, None, '1']
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217165000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217165000, book['time'])
        # check asks
        self.assertEqual(1616965217165000, book['ask_time0'])
        self.assertEqual(2.46, book['ask_px0'])
        self.assertEqual(2300000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217164000, book['ask_time1'])
        self.assertEqual(2.47, book['ask_px1'])
        self.assertEqual(1300000, book['ask_size1'])
        self.assertEqual(b'1', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        # no change to bids
        self.assertEqual(1616965217161000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(2400000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217162000, book['bid_time1'])
        self.assertEqual(2.43, book['bid_px1'])
        self.assertEqual(1200000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        np.savetxt('/tmp/book_eurusd_0010.csv', book, delimiter=',', fmt='%s')


# 5.) w <- as expected - prices and times should be the same - but new book snap

    # EUR/USD
    #                   bids | asks
    # [1] 2400000 @ 2.45 lp0 | [1] 2300000 @ 2.46 lp1
    # [0] 1200000 @ 2.43 lp0 | [0] 1300000 @ 2.47 lp1
    def test_snapshot_no_changes_1(self):
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.43, 'size': 1200000.0, 'provider': '0', 'time': 1616965217162000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1300000.0, 'provider': '1', 'time': 1616965217164000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2400000.0, 'provider': '0', 'time': 1616965217161000},
            'S1': {'entry_type': 1, 'price': 2.46, 'size': 2300000.0, 'provider': '1', 'time': 1616965217165000}
        }
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=4|49=XC461|52=20210328-21:00:17.166|56=Q000|55=EUR/USD|262=0|268=4|269=0|270=2.43|271=1200000|299=0|106=0|269=1|270=2.47|271=1300000|299=0|106=1|269=0|270=2.45|271=2400000|299=1|106=0|269=1|270=2.46|271=2300000|299=1|106=1|10=215|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217166000, 'EURUSD', [
            ['0', 1200000.0, 1300000.0, 2.43, 2.47, '0', '1'],
            ['1', 2400000.0, 2300000.0, 2.45, 2.46, '0', '1'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217166000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217166000, book['time'])
        # no change to bids
        self.assertEqual(1616965217161000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(2400000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217162000, book['bid_time1'])
        self.assertEqual(2.43, book['bid_px1'])
        self.assertEqual(1200000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # no change to asks
        self.assertEqual(1616965217165000, book['ask_time0'])
        self.assertEqual(2.46, book['ask_px0'])
        self.assertEqual(2300000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217164000, book['ask_time1'])
        self.assertEqual(2.47, book['ask_px1'])
        self.assertEqual(1300000, book['ask_size1'])
        self.assertEqual(b'1', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])

        np.savetxt('/tmp/book_eurusd_0011.csv', book, delimiter=',', fmt='%s')

    # USD/CAD
    #                   bids | asks
    # [0] 2200000 @ 1.47 lp0 | [0] 1100000 @ 1.49 lp1 *** asks could be either way around
    # [1] 2200000 @ 1.46 lp1 | [1] 1100000 @ 1.49 lp0
    def test_snapshot_no_changes_2(self):
        self.bookbuilder.quotes['USDCAD'] = {
            'B0': {'entry_type': 0, 'price': 1.47, 'size': 2200000.0, 'provider': '0', 'time': 1616965217159000},
            'S0': {'entry_type': 1, 'price': 1.49, 'size': 1100000.0, 'provider': '0', 'time': 1616965217159000},
            'B1': {'entry_type': 0, 'price': 1.46, 'size': 2200000.0, 'provider': '1', 'time': 1616965217159000},
            'S1': {'entry_type': 1, 'price': 1.49, 'size': 1100000.0, 'provider': '1', 'time': 1616965217159000}
        }
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=5|49=XC461|52=20210328-21:00:17.168|56=Q000|55=USD/CAD|262=1|268=4|269=0|270=1.47|271=2200000|299=0|106=0|269=1|270=1.49|271=1100000|299=0|106=0|269=0|270=1.46|271=2200000|299=1|106=1|269=1|270=1.49|271=1100000|299=1|106=1|10=183|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217168000, 'USDCAD', [
            ['0', 2200000.0, 1100000.0, 1.47, 1.49, '0', '0'],
            ['1', 2200000.0, 1100000.0, 1.46, 1.49, '1', '1'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217168000, time)
        self.assertEqual('USDCAD', symbol)
        # no changes to bids or asks
        self.assertEqual(1616965217168000, book['time'])
        self.assertEqual(1616965217159000, book['bid_time0'])
        self.assertEqual(1.47, book['bid_px0'])
        self.assertEqual(2200000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217159000, book['bid_time1'])
        self.assertEqual(1.46, book['bid_px1'])
        self.assertEqual(2200000, book['bid_size1'])
        self.assertEqual(b'1', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        self.assertEqual(1616965217159000, book['ask_time0'])
        self.assertEqual(1.49, book['ask_px0'])
        self.assertEqual(1100000, book['ask_size0'])
        self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(1616965217159000, book['ask_time1'])
        self.assertEqual(1.49, book['ask_px1'])
        self.assertEqual(1100000, book['ask_size1'])
        self.assertEqual(b'1', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_usdcad_0012.csv', book, delimiter=',', fmt='%s')

# 6.) single-sided snapshot

## snapshot, only 1 bid

    # EUR/USD
    #                   bids | asks
    # [1] 1000000 @ 2.44 lp0 |
    def test_snapshot_only_bid(self):
        self.bookbuilder.quotes['EURUSD'] = {
            'B0': {'entry_type': 0, 'price': 2.43, 'size': 1200000.0, 'provider': '0', 'time': 1616965217162000},
            'S0': {'entry_type': 1, 'price': 2.47, 'size': 1300000.0, 'provider': '1', 'time': 1616965217164000},
            'B1': {'entry_type': 0, 'price': 2.45, 'size': 2400000.0, 'provider': '0', 'time': 1616965217161000},
            'S1': {'entry_type': 1, 'price': 2.46, 'size': 2300000.0, 'provider': '1', 'time': 1616965217165000}
        }

        msg = fix.Message('8=FIX.4.4|9=114|35=W|34=4|49=XC461|52=20210328-21:00:17.170|56=Q000|55=EUR/USD|262=0|268=1|269=0|270=2.44|271=1000000|299=1|106=0|10=237|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217170000, 'EURUSD', [
            ['1', 1000000.0, None, 2.44, None, '0', None],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217170000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217170000, book['time'])
        self.assertEqual(1616965217170000, book['bid_time0'])
        self.assertEqual(2.44, book['bid_px0'])
        self.assertEqual(1000000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(0, book['bid_time1'])
        self.assertEqual(0, book['bid_px1'])
        self.assertEqual(0, book['bid_size1'])
        self.assertEqual(b'', book['bid_provider1'][0])
        # empty ask
        self.assertEqual(0, book['ask_time0'])
        self.assertEqual(0, book['ask_px0'])
        self.assertEqual(0, book['ask_size0'])
        self.assertEqual(b'', book['ask_provider0'][0])
        np.savetxt('/tmp/book_eurusd_0013.csv', book, delimiter=',', fmt='%s')

## snapshot, only 1 ask
    # EUR/USD
    #                   bids | asks
    #                        | [0] 1000000 @ 2.48 lp1
    def test_snapshot_only_ask(self):
        self.bookbuilder.quotes['EURUSD'] = {
            'B1': {'entry_type': 0, 'price': 2.44, 'size': 1000000.0, 'provider': '0', 'time': 1616965217170000}
        }

        msg = fix.Message('8=FIX.4.4|9=114|35=W|34=4|49=XC461|52=20210328-21:00:17.171|56=Q000|55=EUR/USD|262=0|268=1|269=1|270=2.48|271=1000000|299=0|106=1|10=243|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217171000, 'EURUSD', [
            ['0', None, 1000000.0, None, 2.48, None, '1'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217171000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965217171000, book['time'])
        # empty bid
        self.assertEqual(0, book['bid_time0'])
        self.assertEqual(0, book['bid_px0'])
        self.assertEqual(0, book['bid_size0'])
        self.assertEqual(b'', book['bid_provider0'][0])
        # only one layer of asks
        self.assertEqual(1616965217171000, book['ask_time0'])
        self.assertEqual(2.48, book['ask_px0'])
        self.assertEqual(1000000.0, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(0, book['ask_time1'])
        self.assertEqual(0, book['ask_px1'])
        self.assertEqual(0, book['ask_size1'])
        self.assertEqual(b'', book['ask_provider1'][0])
        np.savetxt('/tmp/book_eurusd_0014.csv', book, delimiter=',', fmt='%s')

# 7.) w <- different price/feed/quantity - all combinations as in i

    # USD/CAD
    #                   bids | asks
    # [0] 2300000 @ 1.37 lp1 | [0] 1200000 @ 1.39 lp0
    # [1] 2300000 @ 1.36 lp0 | [1] 1200000 @ 1.40 lp1
    def test_snapshot_change_all_prices_sizes_and_providers(self):
        self.bookbuilder.quotes['USDCAD'] = {
            'B0': {'entry_type': 0, 'price': 1.47, 'size': 2200000.0, 'provider': '0', 'time': 1616965217168000},
            'S0': {'entry_type': 1, 'price': 1.49, 'size': 1100000.0, 'provider': '0', 'time': 1616965217168000},
            'B1': {'entry_type': 0, 'price': 1.46, 'size': 2200000.0, 'provider': '1', 'time': 1616965217168000},
            'S1': {'entry_type': 1, 'price': 1.49, 'size': 1100000.0, 'provider': '1', 'time': 1616965217168000}
        }
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=5|49=XC461|52=20210328-21:00:17.180|56=Q000|55=USD/CAD|262=1|268=4|269=0|270=1.37|271=2300000|299=0|106=1|269=1|270=1.40|271=1200000|299=0|106=1|269=0|270=1.36|271=2300000|299=1|106=0|269=1|270=1.39|271=1200000|299=1|106=0|10=169|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217180000, 'USDCAD', [
            ['0', 2300000.0, 1200000.0, 1.37, 1.40, '1', '1'],
            ['1', 2300000.0, 1200000.0, 1.36, 1.39, '0', '0'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217180000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965217180000, book['time'])
        # check bids
        self.assertEqual(1616965217180000, book['bid_time0'])
        self.assertEqual(1.37, book['bid_px0'])
        self.assertEqual(2300000, book['bid_size0'])
        self.assertEqual(b'1', book['bid_provider0'][0])
        self.assertEqual(1616965217180000, book['bid_time1'])
        self.assertEqual(1.36, book['bid_px1'])
        self.assertEqual(2300000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # check asks
        self.assertEqual(1616965217180000, book['ask_time0'])
        self.assertEqual(1.39, book['ask_px0'])
        self.assertEqual(1200000, book['ask_size0'])
        self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(1616965217180000, book['ask_time1'])
        self.assertEqual(1.40, book['ask_px1'])
        self.assertEqual(1200000, book['ask_size1'])
        self.assertEqual(b'1', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_usdcad_0015.csv', book, delimiter=',', fmt='%s')

    # USD/CAD
    #                   bids | asks
    # [0] 2100000*@ 1.37 lp1 | [0] 1400000*@ 1.39 lp0
    # [1] 2200000*@ 1.36 lp0 | [1] 1300000*@ 1.40 lp1
    def test_snapshot_change_all_sizes(self):
        self.bookbuilder.quotes['USDCAD'] = {
            'B0': {'entry_type': 0, 'price': 1.37, 'size': 2300000.0, 'provider': '1', 'time': 1616965217180000},
            'S0': {'entry_type': 1, 'price': 1.40, 'size': 1200000.0, 'provider': '1', 'time': 1616965217180000},
            'B1': {'entry_type': 0, 'price': 1.36, 'size': 2300000.0, 'provider': '0', 'time': 1616965217180000},
            'S1': {'entry_type': 1, 'price': 1.39, 'size': 1200000.0, 'provider': '0', 'time': 1616965217180000}
        }
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=5|49=XC461|52=20210328-21:00:17.181|56=Q000|55=USD/CAD|262=1|268=4|269=0|270=1.37|271=2100000|299=0|106=1|269=1|270=1.40|271=1300000|299=0|106=1|269=0|270=1.36|271=2200000|299=1|106=0|269=1|270=1.39|271=1400000|299=1|106=0|10=170|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217181000, 'USDCAD', [
            ['0', 2100000.0, 1300000.0, 1.37, 1.40, '1', '1'],
            ['1', 2200000.0, 1400000.0, 1.36, 1.39, '0', '0'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217181000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965217181000, book['time'])
        # check bids
        self.assertEqual(1616965217181000, book['bid_time0'])
        self.assertEqual(1.37, book['bid_px0'])
        self.assertEqual(2100000, book['bid_size0'])
        self.assertEqual(b'1', book['bid_provider0'][0])
        self.assertEqual(1616965217181000, book['bid_time1'])
        self.assertEqual(1.36, book['bid_px1'])
        self.assertEqual(2200000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # check asks
        self.assertEqual(1616965217181000, book['ask_time0'])
        self.assertEqual(1.39, book['ask_px0'])
        self.assertEqual(1400000, book['ask_size0'])
        self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(1616965217181000, book['ask_time1'])
        self.assertEqual(1.40, book['ask_px1'])
        self.assertEqual(1300000, book['ask_size1'])
        self.assertEqual(b'1', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        # print(self.bookbuilder.quotes['USDCAD'])
        np.savetxt('/tmp/book_usdcad_0016.csv', book, delimiter=',', fmt='%s')

    # USD/CAD
    #                   bids | asks
    # [0] 2200000 @ 1.35*lp1 | [0] 1400000 @ 1.35*lp0
    # [1] 2100000 @ 1.35*lp0 | [1] 1300000 @ 1.35*lp1
    def test_snapshot_change_all_prices(self):
        self.bookbuilder.quotes['USDCAD'] = {
            'B0': {'entry_type': 0, 'price': 1.37, 'size': 2100000.0, 'provider': '1', 'time': 1616965217181000},
            'S0': {'entry_type': 1, 'price': 1.40, 'size': 1300000.0, 'provider': '1', 'time': 1616965217181000},
            'B1': {'entry_type': 0, 'price': 1.36, 'size': 2200000.0, 'provider': '0', 'time': 1616965217181000},
            'S1': {'entry_type': 1, 'price': 1.39, 'size': 1400000.0, 'provider': '0', 'time': 1616965217181000}
        }
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=5|49=XC461|52=20210328-21:00:17.182|56=Q000|55=USD/CAD|262=1|268=4|269=0|270=1.35|271=2100000|299=0|106=1|269=1|270=1.35|271=1300000|299=0|106=1|269=0|270=1.35|271=2200000|299=1|106=0|269=1|270=1.35|271=1400000|299=1|106=0|10=168|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217182000, 'USDCAD', [
            ['0', 2100000.0, 1300000.0, 1.35, 1.35, '1', '1'],
            ['1', 2200000.0, 1400000.0, 1.35, 1.35, '0', '0'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217182000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965217182000, book['time'])
        # check bids
        self.assertEqual(1616965217182000, book['bid_time0'])
        self.assertEqual(1.35, book['bid_px0'])
        self.assertEqual(2200000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217182000, book['bid_time1'])
        self.assertEqual(1.35, book['bid_px1'])
        self.assertEqual(2100000, book['bid_size1'])
        self.assertEqual(b'1', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # check asks
        self.assertEqual(1616965217182000, book['ask_time0'])
        self.assertEqual(1.35, book['ask_px0'])
        # FIXME: we should sort sizes descending always...
        # self.assertEqual(1400000, book['ask_size0'])
        # self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(1616965217182000, book['ask_time1'])
        self.assertEqual(1.35, book['ask_px1'])
        # FIXME: we should sort sizes descending always...
        # self.assertEqual(1300000, book['ask_size1'])
        # self.assertEqual(b'1', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_usdcad_0017.csv', book, delimiter=',', fmt='%s')


    # USD/CAD
    #                   bids | asks
    # [1] 2100000 @ 1.34*lp0 | [1] 1500000 @ 1.34*lp1
    # [0] 2000000 @ 1.34*lp1 | [0] 1200000 @ 1.34*lp0
    def test_snapshot_change_all_prices_and_sizes(self):
        self.bookbuilder.quotes['USDCAD'] = {
            'B0': {'entry_type': 0, 'price': 1.35, 'size': 2100000.0, 'provider': '1', 'time': 1616965217182000},
            'S0': {'entry_type': 1, 'price': 1.35, 'size': 1300000.0, 'provider': '1', 'time': 1616965217182000},
            'B1': {'entry_type': 0, 'price': 1.35, 'size': 2200000.0, 'provider': '0', 'time': 1616965217182000},
            'S1': {'entry_type': 1, 'price': 1.35, 'size': 1400000.0, 'provider': '0', 'time': 1616965217182000}
        }
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=5|49=XC461|52=20210328-21:00:17.185|56=Q000|55=USD/CAD|262=1|268=4|269=0|270=1.34|271=2000000|299=0|106=1|269=1|270=1.34|271=1500000|299=0|106=1|269=0|270=1.34|271=2100000|299=1|106=0|269=1|270=1.34|271=1200000|299=1|106=0|10=165|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217185000, 'USDCAD', [
            ['0', 2000000.0, 1500000.0, 1.34, 1.34, '1', '1'],
            ['1', 2100000.0, 1200000.0, 1.34, 1.34, '0', '0'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217185000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965217185000, book['time'])
        # check bids
        self.assertEqual(1616965217185000, book['bid_time0'])
        self.assertEqual(1.34, book['bid_px0'])
        self.assertEqual(2100000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965217185000, book['bid_time1'])
        self.assertEqual(1.34, book['bid_px1'])
        self.assertEqual(2000000, book['bid_size1'])
        self.assertEqual(b'1', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # check asks
        self.assertEqual(1616965217185000, book['ask_time0'])
        self.assertEqual(1.34, book['ask_px0'])
        self.assertEqual(1500000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965217185000, book['ask_time1'])
        self.assertEqual(1.34, book['ask_px1'])
        self.assertEqual(1200000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_usdcad_0018.csv', book, delimiter=',', fmt='%s')

    # USD/CAD
    #                   bids | asks
    # [1] 2100000 @ 1.34 lp1*| [0] 1500000 @ 1.34 lp0*
    # [0] 2000000 @ 1.34 lp0*| [1] 1200000 @ 1.34 lp1*
    def test_snapshot_change_all_providers(self):
        self.bookbuilder.quotes['USDCAD'] = {
            'B0': {'entry_type': 0, 'price': 1.34, 'size': 2000000.0, 'provider': '1', 'time': 1616965217185000},
            'S0': {'entry_type': 1, 'price': 1.34, 'size': 1500000.0, 'provider': '1', 'time': 1616965217185000},
            'B1': {'entry_type': 0, 'price': 1.34, 'size': 2100000.0, 'provider': '0', 'time': 1616965217185000},
            'S1': {'entry_type': 1, 'price': 1.34, 'size': 1200000.0, 'provider': '0', 'time': 1616965217185000}
        }
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=5|49=XC461|52=20210328-21:00:17.186|56=Q000|55=USD/CAD|262=1|268=4|269=0|270=1.34|271=2000000|299=0|106=0|269=1|270=1.34|271=1500000|299=0|106=0|269=0|270=1.34|271=2100000|299=1|106=1|269=1|270=1.34|271=1200000|299=1|106=1|10=166|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217186000, 'USDCAD', [
            ['0', 2000000.0, 1500000.0, 1.34, 1.34, '0', '0'],
            ['1', 2100000.0, 1200000.0, 1.34, 1.34, '1', '1'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217186000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965217186000, book['time'])
        # check bids
        self.assertEqual(1616965217186000, book['bid_time0'])
        self.assertEqual(1.34, book['bid_px0'])
        self.assertEqual(2100000, book['bid_size0'])
        self.assertEqual(b'1', book['bid_provider0'][0])
        self.assertEqual(1616965217186000, book['bid_time1'])
        self.assertEqual(1.34, book['bid_px1'])
        self.assertEqual(2000000, book['bid_size1'])
        self.assertEqual(b'0', book['bid_provider1'][0])
        self.assertEqual(0, book['bid_time2'])
        self.assertEqual(0, book['bid_px2'])
        self.assertEqual(0, book['bid_size2'])
        self.assertEqual(b'', book['bid_provider2'][0])
        # check asks
        self.assertEqual(1616965217186000, book['ask_time0'])
        self.assertEqual(1.34, book['ask_px0'])
        self.assertEqual(1500000, book['ask_size0'])
        self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(1616965217186000, book['ask_time1'])
        self.assertEqual(1.34, book['ask_px1'])
        self.assertEqual(1200000, book['ask_size1'])
        self.assertEqual(b'1', book['ask_provider1'][0])
        self.assertEqual(0, book['ask_time2'])
        self.assertEqual(0, book['ask_px2'])
        self.assertEqual(0, book['ask_size2'])
        self.assertEqual(b'', book['ask_provider2'][0])
        np.savetxt('/tmp/book_usdcad_0019.csv', book, delimiter=',', fmt='%s')

## snapshot updates to 1 layer
    # USD/CAD
    #                   bids | asks
    # [1] 2100000 @ 1.34 lp1 | [1] 1200000 @ 1.34 lp1
    def test_snapshot_reduce_to_one_level(self):
        self.bookbuilder.quotes['USDCAD'] = {
            'B0': {'entry_type': 0, 'price': 1.34, 'size': 2000000.0, 'provider': '0', 'time': 1616965217186000},
            'S0': {'entry_type': 1, 'price': 1.34, 'size': 1500000.0, 'provider': '0', 'time': 1616965217186000},
            'B1': {'entry_type': 0, 'price': 1.34, 'size': 2100000.0, 'provider': '1', 'time': 1616965217186000},
            'S1': {'entry_type': 1, 'price': 1.34, 'size': 1200000.0, 'provider': '1', 'time': 1616965217186000}
        }
        msg = fix.Message('8=FIX.4.4|9=153|35=W|34=5|49=XC461|52=20210328-21:00:17.187|56=Q000|55=USD/CAD|262=1|268=2|269=0|270=1.34|271=2100000|299=1|106=1|269=1|270=1.34|271=1200000|299=1|106=1|10=201|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965217187000, 'USDCAD', [
            ['1', 2100000.0, 1200000.0, 1.34, 1.34, '1', '1'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965217187000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965217187000, book['time'])
        # check bids
        self.assertEqual(1616965217186000, book['bid_time0'])
        self.assertEqual(1.34, book['bid_px0'])
        self.assertEqual(2100000, book['bid_size0'])
        self.assertEqual(b'1', book['bid_provider0'][0])
        self.assertEqual(0, book['bid_time1'])
        self.assertEqual(0, book['bid_px1'])
        self.assertEqual(0, book['bid_size1'])
        self.assertEqual(b'', book['bid_provider1'][0])
        # check asks
        self.assertEqual(1616965217186000, book['ask_time0'])
        self.assertEqual(1.34, book['ask_px0'])
        self.assertEqual(1200000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(0, book['ask_time1'])
        self.assertEqual(0, book['ask_px1'])
        self.assertEqual(0, book['ask_size1'])
        self.assertEqual(b'', book['ask_provider1'][0])
        np.savetxt('/tmp/book_usdcad_0020.csv', book, delimiter=',', fmt='%s')

# 8.) logout
    def test_logout(self):
        msg = fix.Message('8=FIX.4.4|9=55|35=5|34=2820|49=Q000|52=20210328-06:43:54.543|56=XC461|10=145|'.replace('|', '\x01'), self.data_dictionary)
        # TODO: clear bookstate

# 9.) logon
    def test_logon2(self):
        msg = fix.Message('8=FIX.4.4|9=106|35=A|34=1|49=Q000|52=20210328-21:01:17.187|56=XC461|553=primexm_TradeFeedr_q|554=******|98=0|108=30|141=Y|10=41|'.replace('|', '\x01'), self.data_dictionary)
        # nothing to do here (callback for offline?)

# 10.) v x 2
    def test_subscribe2(self):
        sub1 = fix.Message('8=FIX.4.4|9=112|35=V|34=2|49=Q000|52=20210328-21:02:00.516|56=XC461|262=0|263=1|264=16|265=1|146=1|55=EUR/USD|267=2|269=0|269=1|10=119|'.replace('|', '\x01'), self.data_dictionary)
        sub2 = fix.Message('8=FIX.4.4|9=112|35=V|34=3|49=Q000|52=20210328-21:02:00.516|56=XC461|262=1|263=1|264=16|265=1|146=1|55=USD/CAD|267=2|269=0|269=1|10=85|'.replace('|', '\x01'), self.data_dictionary)
        # nothing to do here (callback for offline?)

## mass quote, add id 0 (should be the only prices in book)

    # USD/CAD
    #                   bids | asks
    # [0] 1000000 @ 1.33 lp0*| [0] 1100000 @ 1.35 lp0*
    def test_mass_quote_freshly_cleared_book(self):
        msg = fix.Message('8=FIX.4.4|9=124|35=i|34=6|49=XC461|52=20210328-21:02:17.157|56=Q000|296=1|302=1|295=1|299=0|106=0|134=1000000|135=1100000|188=1.33|190=1.35|10=33|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['1'] = 'USDCAD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965337157000, 'USDCAD', [
            ['0', 1000000.0, 1100000.0, 1.33, 1.35, '0', '0'],
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965337157000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965337157000, book['time'])
        # check bids
        self.assertEqual(1616965337157000, book['bid_time0'])
        self.assertEqual(1.33, book['bid_px0'])
        self.assertEqual(1000000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(0, book['bid_time1'])
        self.assertEqual(0, book['bid_px1'])
        self.assertEqual(0, book['bid_size1'])
        self.assertEqual(b'', book['bid_provider1'][0])
        # check asks
        self.assertEqual(1616965337157000, book['ask_time0'])
        self.assertEqual(1.35, book['ask_px0'])
        self.assertEqual(1100000, book['ask_size0'])
        self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(0, book['ask_time1'])
        self.assertEqual(0, book['ask_px1'])
        self.assertEqual(0, book['ask_size1'])
        self.assertEqual(b'', book['ask_provider1'][0])
        np.savetxt('/tmp/book_usdcad_0021.csv', book, delimiter=',', fmt='%s')


## snapshot, two levels, should update both entries

    # EUR/USD
    #                   bids | asks
    # [1] 1000000*@ 2.45*lp0*| [0] 1000000*@ 2.48*lp1*
    # [0] 2000000*@ 2.44*lp1*| [1] 2000000*@ 2.49*lp0*
    def test_snapshot_freshly_cleared_book(self):
        msg = fix.Message('8=FIX.4.4|9=231|35=W|34=4|49=XC461|52=20210328-21:02:17.158|56=Q000|55=EUR/USD|262=0|268=4|269=0|270=2.44|271=2000000|299=0|106=1|269=1|270=2.48|271=1000000|299=0|106=1|269=0|270=2.45|271=1000000|299=1|106=0|269=1|270=2.49|271=2000000|299=1|106=0|10=211|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.on_market_data_snapshot(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965337158000, 'EURUSD', [
            ['0', 2000000.0, 1000000.0, 2.44, 2.48, '1', '1'],
            ['1', 1000000.0, 2000000.0, 2.45, 2.49, '0', '0'],
        ], True), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965337158000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965337158000, book['time'])
        # check bids
        self.assertEqual(1616965337158000, book['bid_time0'])
        self.assertEqual(2.45, book['bid_px0'])
        self.assertEqual(1000000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(1616965337158000, book['bid_time1'])
        self.assertEqual(2.44, book['bid_px1'])
        self.assertEqual(2000000, book['bid_size1'])
        self.assertEqual(b'1', book['bid_provider1'][0])
        # check asks
        self.assertEqual(1616965337158000, book['ask_time0'])
        self.assertEqual(2.48, book['ask_px0'])
        self.assertEqual(1000000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(1616965337158000, book['ask_time1'])
        self.assertEqual(2.49, book['ask_px1'])
        self.assertEqual(2000000, book['ask_size1'])
        self.assertEqual(b'0', book['ask_provider1'][0])
        np.savetxt('/tmp/book_eurusd_0022.csv', book, delimiter=',', fmt='%s')

# 11.) v x 2
    # swap subscriptions
    def test_subscribe3(self):
        sub1 = fix.Message('8=FIX.4.4|9=112|35=V|34=2|49=Q000|52=20210328-21:03:00.516|56=XC461|262=1|263=1|264=16|265=1|146=1|55=EUR/USD|267=2|269=0|269=1|10=121|'.replace('|', '\x01'), self.data_dictionary)
        sub2 = fix.Message('8=FIX.4.4|9=112|35=V|34=3|49=Q000|52=20210328-21:03:00.516|56=XC461|262=0|263=1|264=16|265=1|146=1|55=USD/CAD|267=2|269=0|269=1|10=85|'.replace('|', '\x01'), self.data_dictionary)
        # nothing to do here (callback for offline to update subs?)

# 12.) i - one change x 2 crosses

    # USD/CAD
    #                   bids | asks
    # [0] 1000000 @ 1.33 lp0*| [0] 1100000 @ 1.35 lp0*
    def test_mass_quote_freshly_cleared_book2(self):
        msg = fix.Message('8=FIX.4.4|9=124|35=i|34=6|49=XC461|52=20210328-21:03:17.157|56=Q000|296=1|302=0|295=1|299=0|106=0|134=1000000|135=1100000|188=1.33|190=1.35|10=33|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['0'] = 'USDCAD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965397157000, 'USDCAD', [
            ['0', 1000000.0, 1100000.0, 1.33, 1.35, '0', '0'],
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965397157000, time)
        self.assertEqual('USDCAD', symbol)
        self.assertEqual(1616965397157000, book['time'])
        # check bids
        self.assertEqual(1616965397157000, book['bid_time0'])
        self.assertEqual(1.33, book['bid_px0'])
        self.assertEqual(1000000, book['bid_size0'])
        self.assertEqual(b'0', book['bid_provider0'][0])
        self.assertEqual(0, book['bid_time1'])
        self.assertEqual(0, book['bid_px1'])
        self.assertEqual(0, book['bid_size1'])
        self.assertEqual(b'', book['bid_provider1'][0])
        # check asks
        self.assertEqual(1616965397157000, book['ask_time0'])
        self.assertEqual(1.35, book['ask_px0'])
        self.assertEqual(1100000, book['ask_size0'])
        self.assertEqual(b'0', book['ask_provider0'][0])
        self.assertEqual(0, book['ask_time1'])
        self.assertEqual(0, book['ask_px1'])
        self.assertEqual(0, book['ask_size1'])
        self.assertEqual(b'', book['ask_provider1'][0])
        np.savetxt('/tmp/book_usdcad_0023.csv', book, delimiter=',', fmt='%s')

    # EUR/USD
    #                   bids | asks
    # [1] 2000000*@ 2.33*lp1*| [1] 2100000*@ 2.35*lp1*
    def test_mass_quote_freshly_cleared_book3(self):
        msg = fix.Message('8=FIX.4.4|9=124|35=i|34=6|49=XC461|52=20210328-21:03:17.157|56=Q000|296=1|302=1|295=1|299=1|106=1|134=2000000|135=2100000|188=2.33|190=2.35|10=40|'.replace('|', '\x01'), self.data_dictionary)
        self.pricefeed.active_subscriptions['1'] = 'EURUSD'
        self.pricefeed.on_mass_quote(msg, None)
        item = self.pricefeed.queue.get()
        self.assertEqual((1616965397157000, 'EURUSD', [
            ['1', 2000000.0, 2100000.0, 2.33, 2.35, '1', '1'],
        ], False), item)
        self.bookbuilder.process_item(item)
        time, symbol, book = self.bookbuilder.outbound_queue.get()
        self.assertEqual(1616965397157000, time)
        self.assertEqual('EURUSD', symbol)
        self.assertEqual(1616965397157000, book['time'])
        # check bids
        self.assertEqual(1616965397157000, book['bid_time0'])
        self.assertEqual(2.33, book['bid_px0'])
        self.assertEqual(2000000, book['bid_size0'])
        self.assertEqual(b'1', book['bid_provider0'][0])
        self.assertEqual(0, book['bid_time1'])
        self.assertEqual(0, book['bid_px1'])
        self.assertEqual(0, book['bid_size1'])
        self.assertEqual(b'', book['bid_provider1'][0])
        # check asks
        self.assertEqual(1616965397157000, book['ask_time0'])
        self.assertEqual(2.35, book['ask_px0'])
        self.assertEqual(2100000, book['ask_size0'])
        self.assertEqual(b'1', book['ask_provider0'][0])
        self.assertEqual(0, book['ask_time1'])
        self.assertEqual(0, book['ask_px1'])
        self.assertEqual(0, book['ask_size1'])
        self.assertEqual(b'', book['ask_provider1'][0])
        np.savetxt('/tmp/book_eurusd_0024.csv', book, delimiter=',', fmt='%s')


# TODO?
# book has same price/size for 2 levels, send in snapshot updates changes 1 level, does it work?
# mass quote that updates id 0 bid and id 1 ask ?
