import unittest
from unittest.mock import Mock, patch

from queue import Empty

import numpy as np

import app.bookbuilder as bb


class TestBookBuilderClass(unittest.TestCase):

    def setUp(self):
        self.inbound_queue = Mock()
        self.outbound_queue = Mock()
        self.shutdown_event = Mock()
        self.shutdown_consumer = Mock()
        self.bookbuilder = bb.BookBuilder(self.inbound_queue, self.outbound_queue,
                                          self.shutdown_event, self.shutdown_consumer,
                                          max_levels=4)

    def test_run(self):
        self.shutdown_event.is_set = Mock(side_effect=[False, True])
        self.inbound_queue.get = Mock(side_effect=["item"])
        with patch('app.bookbuilder.BookBuilder.process_item') as process_item:
            with patch('app.bookbuilder.BookBuilder.shutdown') as shutdown:
                self.bookbuilder.run()
                process_item.assert_called_once()
                shutdown.assert_called_once()
                self.assertEqual("item", process_item.call_args[0][0])

    def test_run_empty_queue(self):
        self.shutdown_event.is_set = Mock(side_effect=[False, True])
        self.inbound_queue.get = Mock(side_effect=Empty)
        with patch('app.bookbuilder.BookBuilder.process_item') as process_item:
            with patch('app.bookbuilder.BookBuilder.shutdown') as shutdown:
                self.bookbuilder.run()
                process_item.assert_not_called()
                shutdown.assert_called_once()

    def test_shutdown(self):
        # fake 1 item still on the queue
        self.inbound_queue.get = Mock(side_effect=["item", Empty])
        with patch('app.bookbuilder.BookBuilder.process_item') as process_item:
            self.bookbuilder.shutdown()
            process_item.assert_called_once()
            self.assertEqual("item", process_item.call_args[0][0])
            self.shutdown_consumer.set.assert_called_once()
            self.inbound_queue.close.assert_called_once()
            self.inbound_queue.join_thread.assert_called_once()

    def test_process_item(self):
        with patch('app.bookbuilder.update_quotes', side_effect=[dict()]) as update_quotes:
            with patch('app.bookbuilder.build_book') as build_book:
                self.bookbuilder.process_item([1, "symbol", [3, 4, 5]])
                update_quotes.assert_called_with(1, {}, [3, 4, 5])
                build_book.assert_called_once()


class TestBookBuilderFuncs(unittest.TestCase):

    def setUp(self):
        self.time = 1595336924000000
        self.new_time = 1595336925000000
        self.symbol = 'EUR/USD'
        self.dtype = [
            ('time', 'uint64'),
            ('bid_time0', 'uint64'), ('bid_time1', 'uint64'),
            ('bid_time2', 'uint64'), ('bid_time3', 'uint64'),
            ('bid_px0', 'float64'), ('bid_px1', 'float64'),
            ('bid_px2', 'float64'), ('bid_px3', 'float64'),
            ('bid_size0', 'float64'), ('bid_size1', 'float64'),
            ('bid_size2', 'float64'), ('bid_size3', 'float64'),
            ('ask_time0', 'uint64'), ('ask_time1', 'uint64'),
            ('ask_time2', 'uint64'), ('ask_time3', 'uint64'),
            ('ask_px0', 'float64'), ('ask_px1', 'float64'),
            ('ask_px2', 'float64'), ('ask_px3', 'float64'),
            ('ask_size0', 'float64'), ('ask_size1', 'float64'),
            ('ask_size2', 'float64'), ('ask_size3', 'float64')
        ]
        self.schema = np.zeros(1, dtype=self.dtype)
        self.quotes = [
            {'entry_type': 0, 'price': 1.23, 'size': 100, 'time': 1595336923000000},
            {'entry_type': 1, 'price': 2.34, 'size': 400, 'time': 1595336924000000},
            {'entry_type': 1, 'price': 2.33, 'size': 300, 'time': 1595336923000000},
            {'entry_type': 0, 'price': 1.24, 'size': 200, 'time': 1595336924000000},
            {'entry_type': 0, 'price': 1.25, 'size': 300, 'time': 1595336925000000},
            {'entry_type': 1, 'price': 2.32, 'size': 200, 'time': 1595336922000000},
        ]
        self.quote_entry = {
            'entry_type': 0,
            'time': 1,
            'price': 1.25,
            'size': 100
        }

# update_quotes
    # add prices to clean book
    def test_update_quotes_empty_book_bid(self):
        quote = [['1', 100, None, 1.23, None, 'provider1']]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'size': 100,
                                 'time': 1595336924000000}},
                         res)

    def test_update_quotes_empty_book_ask(self):
        quote = [['1', None, 200, None, 2.34, 'provider1']]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.34, 'size': 200,
                                 'time': 1595336924000000}},
                         res)

    def test_update_quotes_empty_book_both(self):
        quote = [['1', 100, 200, 1.23, 2.34, 'provider1']]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(2, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'size': 100,
                                 'time': 1595336924000000},
                          'S1': {'entry_type': 1, 'price': 2.34, 'size': 200,
                                 'time': 1595336924000000}},
                         res)

    # update price
    def test_update_quotes_update_bid_price(self):
        quote = [['1', 100, None, 1.23, None, 'provider1']]
        new_quote = [['1', None, None, 1.24, None, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.24, 'size': 100,
                                 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_ask_price(self):
        quote = [['1', None, 200, None, 2.34, 'provider1']]
        new_quote = [['1', None, None, None, 2.35, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.35, 'size': 200,
                                 'time': 1595336925000000}},
                         res)

    # update size
    def test_update_quotes_update_bid_size(self):
        quote = [['1', 100, None, 1.23, None, 'provider1']]
        new_quote = [['1', 125, None, None, None, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'size': 125,
                                 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_ask_size(self):
        quote = [['1', None, 200, None, 2.34, 'provider1']]
        new_quote = [['1', None, 250, None, None, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.34, 'size': 250,
                                 'time': 1595336925000000}},
                         res)

    # update test_update_quotes_empty_book_both
    def test_update_quotes_update_bid(self):
        quote = [['1', 100, None, 1.23, None, 'provider1']]
        new_quote = [['1', 125, None, 1.24, None, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.24, 'size': 125,
                                 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_ask(self):
        quote = [['1', None, 200, None, 2.34, 'provider1']]
        new_quote = [['1', None, 250, None, 2.35, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.35, 'size': 250,
                                 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_bid_and_ask(self):
        quote = [['1', 100, 200, 1.23, 2.34, 'provider1']]
        new_quote = [['1', 125, 250, 1.24, 2.35, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(2, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.24, 'size': 125,
                                 'time': 1595336925000000},
                          'S1': {'entry_type': 1, 'price': 2.35, 'size': 250,
                                 'time': 1595336925000000}},
                         res)

    # delete quote
    def test_update_quotes_delete_bid(self):
        quote = [['1', 100, None, 1.23, None, 'provider1']]
        new_quote = [['1', -1, None, 1.23, None, 'provider1']]  # if we get a price
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(0, len(res))
        self.assertEqual({}, res)

    def test_update_quotes_delete_bid_multiple_levels(self):
        quote = [['1', 100, None, 1.23, None, 'provider1'], ['2', 250, None, 1.22, None, 'provider1']]
        new_quote = [['1', -1, None, 1.23, None, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B2': {'entry_type': 0, 'price': 1.22, 'size': 250,
                                 'time': 1595336924000000}},
                         res)

    def test_update_quotes_delete_ask(self):
        quote = [['1', None, 200, None, 2.34, 'provider1']]
        new_quote = [['1', None, -1, None, None, 'provider1']]  # if we dont get a price
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(0, len(res))
        self.assertEqual({}, res)

    def test_update_quotes_delete_ask_multiple_levels(self):
        quote = [
            ['1', None, 200, None, 2.34, 'provider1'],
            ['2', None, 250, None, 2.35, 'provider1']
        ]
        new_quote = [['2', None, -1, None, None, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.34, 'size': 200,
                                 'time': 1595336924000000}},
                         res)

    def test_update_quotes_delete_both(self):
        quote = [['1', 100, 200, 1.23, 2.34, 'provider1']]
        new_quote = [['1', -1, -1, None, None, 'provider1']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(0, len(res))
        self.assertEqual({},
                         res)

# build_book
    def test_build_book_single_level_bid(self):
        quotes = [{'entry_type': 0, 'price': 1.23, 'size': 100, 'time': 1595336924000000}]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(1595336924000000, res['bid_time0'])
        self.assertEqual(1.23, res['bid_px0'])
        self.assertEqual(100, res['bid_size0'])
        self.assertEqual(0, res['ask_time0'])
        self.assertEqual(0, res['ask_px0'])
        self.assertEqual(0, res['ask_size0'])

    def test_build_book_single_level_ask(self):
        quotes = [{'entry_type': 1, 'price': 2.34, 'size': 200, 'time': 1595336924000000}]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(0, res['bid_time0'])
        self.assertEqual(0, res['bid_px0'])
        self.assertEqual(0, res['bid_size0'])
        self.assertEqual(1595336924000000, res['ask_time0'])
        self.assertEqual(2.34, res['ask_px0'])
        self.assertEqual(200, res['ask_size0'])

    def test_build_book_single_level_bid_and_ask(self):
        quotes = [
            {'entry_type': 0, 'price': 1.23, 'size': 100, 'time': 1595336924000000},
            {'entry_type': 1, 'price': 2.34, 'size': 200, 'time': 1595336924000000}
            ]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(1595336924000000, res['bid_time0'])
        self.assertEqual(1.23, res['bid_px0'])
        self.assertEqual(100, res['bid_size0'])
        self.assertEqual(1595336924000000, res['ask_time0'])
        self.assertEqual(2.34, res['ask_px0'])
        self.assertEqual(200, res['ask_size0'])

    def test_build_book_multi_level_bid(self):
        quotes = [
            {'entry_type': 0, 'price': 1.23, 'size': 100, 'time': 1595336923000000},
            {'entry_type': 0, 'price': 1.24, 'size': 200, 'time': 1595336924000000},
            {'entry_type': 0, 'price': 1.25, 'size': 300, 'time': 1595336925000000},
            ]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'][0])
        self.assertEqual(1595336925000000, res['bid_time0'])
        self.assertEqual(1.25, res['bid_px0'])
        self.assertEqual(300, res['bid_size0'])
        self.assertEqual(1595336924000000, res['bid_time1'])
        self.assertEqual(1.24, res['bid_px1'])
        self.assertEqual(200, res['bid_size1'])
        self.assertEqual(1595336923000000, res['bid_time2'])
        self.assertEqual(1.23, res['bid_px2'])
        self.assertEqual(100, res['bid_size2'])
        self.assertEqual(0, res['bid_time3'])
        self.assertEqual(0, res['bid_px3'])
        self.assertEqual(0, res['bid_size3'])
        self.assertEqual(0, res['ask_time0'])
        self.assertEqual(0, res['ask_px0'])
        self.assertEqual(0, res['ask_size0'])

    def test_build_book_multi_level_ask(self):
        quotes = [
            {'entry_type': 1, 'price': 2.34, 'size': 400, 'time': 1595336924000000},
            {'entry_type': 1, 'price': 2.33, 'size': 300, 'time': 1595336923000000},
            {'entry_type': 1, 'price': 2.32, 'size': 200, 'time': 1595336922000000},
            ]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(1595336922000000, res['ask_time0'])
        self.assertEqual(2.32, res['ask_px0'])
        self.assertEqual(200, res['ask_size0'])
        self.assertEqual(1595336923000000, res['ask_time1'])
        self.assertEqual(2.33, res['ask_px1'])
        self.assertEqual(300, res['ask_size1'])
        self.assertEqual(1595336924000000, res['ask_time2'])
        self.assertEqual(2.34, res['ask_px2'])
        self.assertEqual(400, res['ask_size2'])
        self.assertEqual(0, res['ask_time3'])
        self.assertEqual(0, res['ask_px3'])
        self.assertEqual(0, res['ask_size3'])
        self.assertEqual(0, res['bid_time0'])
        self.assertEqual(0, res['bid_px0'])
        self.assertEqual(0, res['bid_size0'])

    def test_build_book_multi_level_bid_and_ask(self):
        res = bb.build_book(1595336925000000, self.quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(1595336925000000, res['bid_time0'])
        self.assertEqual(1.25, res['bid_px0'])
        self.assertEqual(300, res['bid_size0'])
        self.assertEqual(1595336924000000, res['bid_time1'])
        self.assertEqual(1.24, res['bid_px1'])
        self.assertEqual(200, res['bid_size1'])
        self.assertEqual(1595336923000000, res['bid_time2'])
        self.assertEqual(1.23, res['bid_px2'])
        self.assertEqual(100, res['bid_size2'])
        self.assertEqual(1595336922000000, res['ask_time0'])
        self.assertEqual(2.32, res['ask_px0'])
        self.assertEqual(200, res['ask_size0'])
        self.assertEqual(1595336923000000, res['ask_time1'])
        self.assertEqual(2.33, res['ask_px1'])
        self.assertEqual(300, res['ask_size1'])
        self.assertEqual(1595336924000000, res['ask_time2'])
        self.assertEqual(2.34, res['ask_px2'])
        self.assertEqual(400, res['ask_size2'])


# create_schema
    def test_create_schema(self):
        res = bb.create_schema(4)
        self.assertEqual(self.dtype, res)

# update_entry
    def test_update_entry_new_entry(self):
        res = bb.update_entry(None, 0, 1, 100, 1.25)
        self.assertEqual(self.quote_entry, res)

    def test_update_entry_update_size(self):
        res = bb.update_entry(self.quote_entry, 0, 1, 200, None)
        self.assertEqual(200, res['size'])
        self.assertEqual(1.25, res['price'])

    def test_update_entry_update_price(self):
        res = bb.update_entry(self.quote_entry, 0, 1, None, 1.35)
        self.assertEqual(100, res['size'])
        self.assertEqual(1.35, res['price'])

    def test_update_entry_update_price_and_size(self):
        res = bb.update_entry(self.quote_entry, 0, 1, 200, 1.35)
        self.assertEqual(200, res['size'])
        self.assertEqual(1.35, res['price'])

    def test_update_entry_delete(self):
        res = bb.update_entry(self.quote_entry, 0, 1, -1, None)
        self.assertEqual(None, res)

# flip_quotes
    def test_flip_quotes_bid_descending(self):
        times, prices, sizes = bb.flip_quotes(self.quotes, 0, True)
        self.assertEqual([1595336925000000, 1595336924000000, 1595336923000000], times)
        self.assertEqual([1.25, 1.24, 1.23], prices)
        self.assertEqual([300, 200, 100], sizes)

    def test_flip_quotes_bid_ascending(self):
        times, prices, sizes = bb.flip_quotes(self.quotes, 0, False)
        self.assertEqual([1595336923000000, 1595336924000000, 1595336925000000], times)
        self.assertEqual([1.23, 1.24, 1.25], prices)
        self.assertEqual([100, 200, 300], sizes)

    def test_flip_quotes_ask_descending(self):
        times, prices, sizes = bb.flip_quotes(self.quotes, 1, True)
        self.assertEqual([1595336924000000, 1595336923000000, 1595336922000000], times)
        self.assertEqual([2.34, 2.33, 2.32], prices)
        self.assertEqual([400, 300, 200], sizes)

    def test_flip_quotes_ask_ascending(self):
        times, prices, sizes = bb.flip_quotes(self.quotes, 1, False)
        self.assertEqual([1595336922000000, 1595336923000000, 1595336924000000], times)
        self.assertEqual([2.32, 2.33, 2.34], prices)
        self.assertEqual([200, 300, 400], sizes)