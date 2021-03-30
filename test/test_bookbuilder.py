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
                self.bookbuilder.process_item([1, "symbol", [3, 4, 5], False])
                update_quotes.assert_called_with(1, {}, [3, 4, 5])
                build_book.assert_called_once()

    def test_process_item_not_snapshot(self):
        with patch('app.bookbuilder.update_quotes', side_effect=[dict()]) as update_quotes:
            with patch('app.bookbuilder.build_book') as build_book:
                self.bookbuilder.quotes["symbol"] = {'a': 1 }
                self.bookbuilder.process_item([1, "symbol", [3, 4, 5], False])
                update_quotes.assert_called_with(1, {'a': 1 }, [3, 4, 5])
                build_book.assert_called_once()

    def test_process_item_snapshot(self):
        with patch('app.bookbuilder.update_quotes', side_effect=[dict()]) as update_quotes:
            with patch('app.bookbuilder.build_book') as build_book:
                self.bookbuilder.quotes["symbol"] = {'a': 1 }
                self.bookbuilder.process_item([1, "symbol", [3, 4, 5], True])
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
            ('bid_provider0', 'S1'), ('bid_provider1', 'S1'),
            ('bid_provider2', 'S1'), ('bid_provider3', 'S1'),
            ('ask_time0', 'uint64'), ('ask_time1', 'uint64'),
            ('ask_time2', 'uint64'), ('ask_time3', 'uint64'),
            ('ask_px0', 'float64'), ('ask_px1', 'float64'),
            ('ask_px2', 'float64'), ('ask_px3', 'float64'),
            ('ask_size0', 'float64'), ('ask_size1', 'float64'),
            ('ask_size2', 'float64'), ('ask_size3', 'float64'),
            ('ask_provider0', 'S1'), ('ask_provider1', 'S1'),
            ('ask_provider2', 'S1'), ('ask_provider3', 'S1'),
        ]
        self.schema = np.zeros(1, dtype=self.dtype)
        self.quotes = [
            {
                'entry_type': 0, 'price': 1.23, 'size': 100,
                'time': 1595336923000000, 'provider': 'a'
            },
            {
                'entry_type': 1, 'price': 2.34, 'size': 400,
                'time': 1595336924000000, 'provider': 'b'
            },
            {
                'entry_type': 1, 'price': 2.33, 'size': 300,
                'time': 1595336923000000, 'provider': 'b'
            },
            {
                'entry_type': 0, 'price': 1.24, 'size': 200,
                'time': 1595336924000000, 'provider': 'b'
            },
            {
                'entry_type': 0, 'price': 1.25, 'size': 300,
                'time': 1595336925000000, 'provider': 'c'
            },
            {
                'entry_type': 1, 'price': 2.32, 'size': 200,
                'time': 1595336922000000, 'provider': 'c'
            },
        ]
        self.quote_entry = {
            'entry_type': 0,
            'time': 1,
            'price': 1.25,
            'provider': 'a',
            'size': 100.0
        }

# update_quotes
    # add prices to clean book
    def test_update_quotes_empty_book_bid(self):
        quote = [['1', 100, None, 1.23, None, 'a', None]]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'provider': 'a',
                                 'size': 100.0, 'time': 1595336924000000}},
                         res)

    def test_update_quotes_empty_book_ask(self):
        quote = [['1', None, 200.0, None, 2.34, None, 'a']]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.34, 'provider': 'a',
                                 'size': 200.0, 'time': 1595336924000000}},
                         res)

    def test_update_quotes_empty_book_both(self):
        quote = [['1', 100, 200, 1.23, 2.34, 'a', 'b']]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(2, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'provider': 'a',
                                 'size': 100, 'time': 1595336924000000},
                          'S1': {'entry_type': 1, 'price': 2.34, 'provider': 'b',
                                 'size': 200, 'time': 1595336924000000}},
                         res)

    def test_update_quotes_empty_book_zero_qty(self):
        quote = [['1', 0.0, None, 1.23, None, 'a', None]]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'provider': 'a',
                                 'size': 0.0, 'time': 1595336924000000}},
                         res)
    # update price
    def test_update_quotes_update_bid_price(self):
        quote = [['1', 100, None, 1.23, None, 'a', None]]
        new_quote = [['1', None, None, 1.24, None, 'a', None]]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.24, 'provider': 'a',
                                 'size': 100, 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_ask_price(self):
        quote = [['1', None, 200, None, 2.34, None, 'a']]
        new_quote = [['1', None, None, None, 2.35, None, 'a']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.35, 'provider': 'a',
                                 'size': 200, 'time': 1595336925000000}},
                         res)

    # update size
    def test_update_quotes_update_bid_size(self):
        quote = [['1', 100, None, 1.23, None, 'a', None]]
        new_quote = [['1', 125, None, None, None, 'a', None]]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'provider': 'a',
                                 'size': 125, 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_ask_size(self):
        quote = [['1', None, 200, None, 2.34, None, 'a']]
        new_quote = [['1', None, 250, None, None, None, 'a']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.34, 'provider': 'a',
                                 'size': 250, 'time': 1595336925000000}},
                         res)

    # update provider (?)
    # def test_update_quotes_update_provider(self):
    #     quote = [['1', 100, None, 1.23, None, 'a', None]]
    #     new_quote = [['1', None, None, None, None, 'b', None]]
    #     quotes = bb.update_quotes(self.time, {}, quote)
    #     res = bb.update_quotes(self.new_time, quotes, new_quote)
    #     self.assertEqual(1, len(res))
    #     self.assertEqual({'B1': {'entry_type': 0, 'price': 1.23, 'provider': 'b',
    #                              'size': 100, 'time': 1595336925000000}},
    #                      res)

    # update both price and size
    def test_update_quotes_update_bid(self):
        quote = [['1', 100, None, 1.23, None, 'a', None]]
        new_quote = [['1', 125, None, 1.24, None, 'b', None]]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.24, 'provider': 'b',
                                 'size': 125, 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_ask(self):
        quote = [['1', None, 200, None, 2.34, None, 'a']]
        new_quote = [['1', None, 250, None, 2.35, None, 'b']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.35, 'provider': 'b',
                                 'size': 250, 'time': 1595336925000000}},
                         res)

    def test_update_quotes_update_bid_and_ask(self):
        quote = [['1', 100, 200, 1.23, 2.34, 'a', 'a']]
        new_quote = [['1', 125, 250, 1.24, 2.35, 'c', 'b']]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(2, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 1.24, 'provider': 'c',
                                 'size': 125, 'time': 1595336925000000},
                          'S1': {'entry_type': 1, 'price': 2.35, 'provider': 'b',
                                 'size': 250, 'time': 1595336925000000}},
                         res)

    def test_update_quotes_zero_price_and_size(self):
        quote = [['1', 0.0, 0.0, 0.0, 0.0, 'a', 'b']]
        res = bb.update_quotes(self.time, {}, quote)
        self.assertEqual(2, len(res))
        self.assertEqual({'B1': {'entry_type': 0, 'price': 0.0, 'provider': 'a',
                                 'size': 0.0, 'time': 1595336924000000},
                          'S1': {'entry_type': 1, 'price': 0.0, 'provider': 'b',
                                 'size': 0.0, 'time': 1595336924000000}},
                         res)

    # delete quote
    def test_update_quotes_delete_bid(self):
        quote = [['1', 100, None, 1.23, None, 'a', None]]
        new_quote = [['1', -1, None, 1.23, None, None, None]]  # if we get a price
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(0, len(res))
        self.assertEqual({}, res)

    def test_update_quotes_delete_bid_multiple_levels(self):
        quote = [
            ['1', 100, None, 1.23, None, 'a', None],
            ['2', 250, None, 1.22, None, 'b', None]
        ]
        new_quote = [['1', -1, None, 1.23, None, None, None]]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'B2': {'entry_type': 0, 'price': 1.22, 'provider': 'b',
                                 'size': 250, 'time': 1595336924000000}},
                         res)

    def test_update_quotes_delete_ask(self):
        quote = [['1', None, 200, None, 2.34, None, 'a']]
        new_quote = [['1', None, -1, None, None, None, None]]  # if we dont get a price
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(0, len(res))
        self.assertEqual({}, res)

    def test_update_quotes_delete_ask_multiple_levels(self):
        quote = [
            ['1', None, 200, None, 2.34, None, 'a'],
            ['2', None, 250, None, 2.35, None, 'b']
        ]
        new_quote = [['2', None, -1, None, None, None, None]]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(1, len(res))
        self.assertEqual({'S1': {'entry_type': 1, 'price': 2.34, 'provider': 'a',
                                 'size': 200, 'time': 1595336924000000}},
                         res)

    def test_update_quotes_delete_both(self):
        quote = [['1', 100, 200, 1.23, 2.34, 'a', 'a']]
        new_quote = [['1', -1, -1, None, None, None, None]]
        quotes = bb.update_quotes(self.time, {}, quote)
        res = bb.update_quotes(self.new_time, quotes, new_quote)
        self.assertEqual(0, len(res))
        self.assertEqual({},
                         res)

# build_book
    def test_build_book_single_level_bid(self):
        quotes = [{'entry_type': 0, 'price': 1.23, 'size': 100,
                   'time': 1595336924000000, 'provider': 'abc'}]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)

        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(1595336924000000, res['bid_time0'])
        self.assertEqual(1.23, res['bid_px0'])
        self.assertEqual(100, res['bid_size0'])
        self.assertEqual(b'a', res['bid_provider0'][0])
        self.assertEqual(0, res['ask_time0'])
        self.assertEqual(0, res['ask_px0'])
        self.assertEqual(0, res['ask_size0'])
        self.assertEqual(b'', res['ask_provider0'])

    def test_build_book_single_level_ask(self):
        quotes = [{'entry_type': 1, 'price': 2.34, 'size': 200,
                   'time': 1595336924000000, 'provider': 'a'}]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(0, res['bid_time0'])
        self.assertEqual(0, res['bid_px0'])
        self.assertEqual(0, res['bid_size0'])
        self.assertEqual(b'', res['bid_provider0'][0])
        self.assertEqual(1595336924000000, res['ask_time0'])
        self.assertEqual(2.34, res['ask_px0'])
        self.assertEqual(200, res['ask_size0'])
        self.assertEqual(b'a', res['ask_provider0'][0])

    def test_build_book_single_level_bid_and_ask(self):
        quotes = [
            {'entry_type': 0, 'price': 1.23, 'size': 100, 'time': 1595336924000000, 'provider': 'a'},
            {'entry_type': 1, 'price': 2.34, 'size': 200, 'time': 1595336924000000, 'provider': 'b'}
            ]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(1595336924000000, res['bid_time0'])
        self.assertEqual(1.23, res['bid_px0'])
        self.assertEqual(100, res['bid_size0'])
        self.assertEqual(b'a', res['bid_provider0'][0])
        self.assertEqual(1595336924000000, res['ask_time0'])
        self.assertEqual(2.34, res['ask_px0'])
        self.assertEqual(200, res['ask_size0'])
        self.assertEqual(b'b', res['ask_provider0'][0])

    def test_build_book_multi_level_bid(self):
        quotes = [
            {
                'entry_type': 0, 'price': 1.23, 'size': 100,
                'time': 1595336923000000, 'provider': 'a'
            },
            {
                'entry_type': 0, 'price': 1.24, 'size': 200,
                'time': 1595336924000000, 'provider': 'b'
            },
            {
                'entry_type': 0, 'price': 1.25, 'size': 300,
                'time': 1595336925000000, 'provider': 'c'
            },
        ]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'][0])
        self.assertEqual(1595336925000000, res['bid_time0'])
        self.assertEqual(1.25, res['bid_px0'])
        self.assertEqual(300, res['bid_size0'])
        self.assertEqual(b'c', res['bid_provider0'][0])
        self.assertEqual(1595336924000000, res['bid_time1'])
        self.assertEqual(1.24, res['bid_px1'])
        self.assertEqual(200, res['bid_size1'])
        self.assertEqual(b'b', res['bid_provider1'][0])
        self.assertEqual(1595336923000000, res['bid_time2'])
        self.assertEqual(1.23, res['bid_px2'])
        self.assertEqual(100, res['bid_size2'])
        self.assertEqual(b'a', res['bid_provider2'][0])
        self.assertEqual(0, res['bid_time3'])
        self.assertEqual(0, res['bid_px3'])
        self.assertEqual(0, res['bid_size3'])
        self.assertEqual(0, res['ask_time0'])
        self.assertEqual(0, res['ask_px0'])
        self.assertEqual(0, res['ask_size0'])
        self.assertEqual(b'', res['ask_provider0'][0])

    def test_build_book_multi_level_ask(self):
        quotes = [
            {'entry_type': 1, 'price': 2.34, 'size': 400,
             'time': 1595336924000000, 'provider': 'a'
            },
            {'entry_type': 1, 'price': 2.33, 'size': 300,
             'time': 1595336923000000, 'provider': 'b'
            },
            {'entry_type': 1, 'price': 2.32, 'size': 200,
             'time': 1595336922000000, 'provider': 'c'
            },
            ]
        res = bb.build_book(1595336925000000, quotes, self.schema, 4)
        self.assertEqual(1595336925000000, res['time'])
        self.assertEqual(1595336922000000, res['ask_time0'])
        self.assertEqual(2.32, res['ask_px0'])
        self.assertEqual(200, res['ask_size0'])
        self.assertEqual(b'c', res['ask_provider0'][0])
        self.assertEqual(1595336923000000, res['ask_time1'])
        self.assertEqual(2.33, res['ask_px1'])
        self.assertEqual(300, res['ask_size1'])
        self.assertEqual(b'b', res['ask_provider1'][0])
        self.assertEqual(1595336924000000, res['ask_time2'])
        self.assertEqual(2.34, res['ask_px2'])
        self.assertEqual(400, res['ask_size2'])
        self.assertEqual(b'a', res['ask_provider2'][0])
        self.assertEqual(0, res['ask_time3'])
        self.assertEqual(0, res['ask_px3'])
        self.assertEqual(0, res['ask_size3'])
        self.assertEqual(b'', res['ask_provider3'][0])
        self.assertEqual(0, res['bid_time0'])
        self.assertEqual(0, res['bid_px0'])
        self.assertEqual(0, res['bid_size0'])
        self.assertEqual(b'', res['bid_provider0'][0])

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
        res = bb.update_entry(None, 0, 1, 100, 1.25, 'a')
        self.assertEqual(self.quote_entry, res)

    def test_update_entry_update_size(self):
        res = bb.update_entry(self.quote_entry, 0, 1, 200, None, 'a')
        self.assertEqual(200, res['size'])
        self.assertEqual(1.25, res['price'])
        self.assertEqual('a', res['provider'])

    def test_update_entry_update_price(self):
        res = bb.update_entry(self.quote_entry, 0, 1, None, 1.35, 'a')
        self.assertEqual(100, res['size'])
        self.assertEqual(1.35, res['price'])
        self.assertEqual('a', res['provider'])

    def test_update_entry_update_price_and_size(self):
        res = bb.update_entry(self.quote_entry, 0, 1, 200, 1.35, 'a')
        self.assertEqual(200, res['size'])
        self.assertEqual(1.35, res['price'])
        self.assertEqual('a', res['provider'])

    def test_update_entry_delete(self):
        res = bb.update_entry(self.quote_entry, 0, 1, -1, None, None)
        self.assertEqual(None, res)

    def test_update_entry_no_provider(self):
        res = bb.update_entry(None, 0, 1, 100, 1.25, None)
        self.assertEqual('', res['provider'])
# flip_quotes
    def test_flip_quotes_bid_descending(self):
        times, prices, sizes, providers = bb.flip_quotes(self.quotes, 0, True)
        self.assertEqual([1595336925000000, 1595336924000000, 1595336923000000], times)
        self.assertEqual([1.25, 1.24, 1.23], prices)
        self.assertEqual([300, 200, 100], sizes)
        self.assertEqual(['c', 'b', 'a'], providers)

    def test_flip_quotes_bid_ascending(self):
        times, prices, sizes, providers = bb.flip_quotes(self.quotes, 0, False)
        self.assertEqual([1595336923000000, 1595336924000000, 1595336925000000], times)
        self.assertEqual([1.23, 1.24, 1.25], prices)
        self.assertEqual([100, 200, 300], sizes)
        self.assertEqual(['a', 'b', 'c'], providers)

    def test_flip_quotes_ask_descending(self):
        times, prices, sizes, providers = bb.flip_quotes(self.quotes, 1, True)
        self.assertEqual([1595336924000000, 1595336923000000, 1595336922000000], times)
        self.assertEqual([2.34, 2.33, 2.32], prices)
        self.assertEqual([400, 300, 200], sizes)
        self.assertEqual(['b', 'b', 'c'], providers)

    def test_flip_quotes_ask_ascending(self):
        times, prices, sizes, providers = bb.flip_quotes(self.quotes, 1, False)
        self.assertEqual([1595336922000000, 1595336923000000, 1595336924000000], times)
        self.assertEqual([2.32, 2.33, 2.34], prices)
        self.assertEqual([200, 300, 400], sizes)
        self.assertEqual(['c', 'b', 'b'], providers)

    def test_flip_quotes_filter_zero_qty(self):
        quotes = [
            {'entry_type': 0, 'price': 1.23, 'size': 5.0, 'time': 1595336923000000, 'provider': 'a'},
            {'entry_type': 0, 'price': 1.24, 'size': 0.0, 'time': 1595336924000000, 'provider': 'b'},
            {'entry_type': 0, 'price': 1.25, 'size': 3.0, 'time': 1595336925000000, 'provider': 'c'},
        ]
        times, prices, sizes, providers = bb.flip_quotes(quotes, 0, False)
        self.assertEqual([1595336923000000, 1595336925000000], times)
        self.assertEqual([1.23, 1.25], prices)
        self.assertEqual([5.0, 3.0], sizes)
        self.assertEqual(['a', 'c'], providers)
