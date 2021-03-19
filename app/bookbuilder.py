import logging

from queue import Empty

import numpy as np

logger = logging.getLogger(__name__)


class BookBuilder():
    def __init__(self,
                 inbound_queue,      # inbound work (from pricefeed)
                 outbound_queue,     # outbound work (to filewriter)
                 shutdown_event,     # publisher shutdown?
                 shutdown_consumer,  # shutdown consumer?
                 max_levels=10):
        logger.info('Initialising Book Builder')
        # queues
        self.inbound_queue = inbound_queue
        self.outbound_queue = outbound_queue
        # events
        self.shutdown_event = shutdown_event
        self.shutdown_consumer = shutdown_consumer
        # setup book format
        assert max_levels > 0
        self.max_levels = max_levels
        self.schema = np.zeros(1, dtype=create_schema(max_levels))
        # internal state
        self.quotes = {}

    def run(self):
        """Consume queue until told to stop"""
        logger.debug('Starting consumption of work queue')
        while not self.shutdown_event.is_set():
            try:
                item = self.inbound_queue.get(block=True, timeout=1)
            except Empty:
                continue
            self.process_item(item)
        self.shutdown()

    def shutdown(self):
        """Perform shutdown related housekeeping"""
        logger.info('Shutdown triggered!')
        while True:
            # drain queue
            try:
                item = self.inbound_queue.get(block=False)
            except Empty:
                break
            self.process_item(item)
        self.inbound_queue.close()
        self.inbound_queue.join_thread()
        logger.info('Triggering shutdown of consumer')
        self.shutdown_consumer.set()
        logger.info('Shutdown complete!')

    def process_item(self, item):
        """Update quotes and publish a book"""
        time, symbol, new_quotes, snapshot = item
        logger.debug('Processing %i new quote(s) for %s @ %s (snapshot: %r)',
                     len(new_quotes), symbol, time, snapshot)

        current_quotes = self.quotes.get(symbol)
        if current_quotes is None:
            logger.debug('First quote of the session for %s', symbol)
            current_quotes = {}
        if snapshot:
            # clear quotes on snapshot
            current_quotes = {}
        # apply updates
        updated_quotes = update_quotes(time, current_quotes, new_quotes)
        # update quote cache
        self.quotes[symbol] = updated_quotes
        # build new book
        book = build_book(time, updated_quotes.values(), np.copy(self.schema), self.max_levels)
        # push book to outbound queue
        self.outbound_queue.put((time, symbol, book))
        # return book to aid testing
        return book


def update_quotes(time, current_quotes, quotes):
    """Process quote updates"""
    for quote in quotes:
        # ignore provider for now
        entry_id, bid_size, ask_size, bid_price, ask_price, _ = quote
        # bid
        if bid_size or bid_price:
            entry_key = 'B' + entry_id
            bid_entry = update_entry(current_quotes.get(entry_key), 0,
                                     time, bid_size, bid_price)
            if bid_entry:
                current_quotes[entry_key] = bid_entry
            else:
                del current_quotes[entry_key]
        # ask
        if ask_size or ask_price:
            entry_key = 'S' + entry_id
            ask_entry = update_entry(current_quotes.get(entry_key), 1,
                                     time, ask_size, ask_price)
            if ask_entry:
                current_quotes[entry_key] = ask_entry
            else:
                del current_quotes[entry_key]
    return current_quotes


def update_entry(quote_entry, entry_type, time, size, price):
    """Helper function to create/update individual quote entry"""
    logger.debug('%r %r %r %r', entry_type, time, size, price)
    if quote_entry is None:
        quote_entry = {'entry_type': entry_type}
    if price is not None:
        quote_entry['price'] = price
    if size is not None:
        if size == -1:
            # fast exit
            return None
        quote_entry['size'] = size
    quote_entry['time'] = time
    return quote_entry


def flip_quotes(quotes, entry_type, descending):
    """Filter and transpose list of dicts into list of sorted lists"""
    # filter based on entry_type
    filtered = list(filter(lambda x: x['entry_type'] == entry_type and x['size'] > 0, quotes))
    # pull out rows into columns
    entries = [[d[k] for d in filtered] for k in ['time', 'price', 'size']]
    entry_times = entries[0]
    entry_prices = entries[1]
    entry_sizes = entries[2]
    # index to sort ascending/descending
    sort_idx = np.argsort(entry_prices)[::-1 if descending else 1]
    # apply sorting
    return ([entry_times[x] for x in sort_idx],
            [entry_prices[x] for x in sort_idx],
            [entry_sizes[x] for x in sort_idx])


def build_book(time, quotes, schema, number_of_levels=10):
    """Constructs a book based on list of quotes"""
    bid_times, bid_prices, bid_sizes = flip_quotes(quotes, 0, True)
    ask_times, ask_prices, ask_sizes = flip_quotes(quotes, 1, False)
    # create schema-like structure
    row = [time] + \
        bid_times[:min(number_of_levels, len(bid_times))] + \
        [0] * (number_of_levels - min(number_of_levels, len(bid_times))) + \
        bid_prices[:min(number_of_levels, len(bid_prices))] + \
        [0] * (number_of_levels - min(number_of_levels, len(bid_prices))) + \
        bid_sizes[:min(number_of_levels, len(bid_sizes))] + \
        [0] * (number_of_levels - min(number_of_levels, len(bid_sizes))) + \
        ask_times[:min(number_of_levels, len(ask_times))] + \
        [0] * (number_of_levels - min(number_of_levels, len(ask_times))) + \
        ask_prices[:min(number_of_levels, len(ask_prices))] + \
        [0] * (number_of_levels - min(number_of_levels, len(ask_prices))) + \
        ask_sizes[:min(number_of_levels, len(ask_sizes))] + \
        [0] * (number_of_levels - min(number_of_levels, len(ask_sizes)))
    schema[0] = tuple(row)
    return schema


def create_schema(levels):
    """Helper function to create empty array to inject quotes into"""
    dtype = []
    dtype.append(('time', 'uint64'))
    column_datetype = [
        ('bid_time', 'uint64'),
        ('bid_px', 'float64'),
        ('bid_size', 'float64'),
        ('ask_time', 'uint64'),
        ('ask_px', 'float64'),
        ('ask_size', 'float64')
        ]
    for column, datatype in column_datetype:
        for i in range(levels):
            dtype.append((column + str(i), datatype))
    return dtype
