"""Helper functions"""

import datetime
import logging

import quickfix as fix
import quickfix44 as fix44

import app.pxm44 as pxm44

# only used for missing subscription error
logger = logging.getLogger(__name__)


def create_market_data_request(request_id, symbol):
    """Construct MarketDataRequest with request_id and symbol"""
    msg = fix44.MarketDataRequest()
    msg.setField(fix.MDReqID(request_id))           # 262 = request id, e.g. 1
    msg.setField(fix.SubscriptionRequestType('1'))  # 263 = 1 = Subscribe
    msg.setField(fix.MarketDepth(0))                # 264 = 0 = Full Book
    group = fix44.MarketDataRequest.NoRelatedSym()  # 146 = 1
    group.setField(fix.Symbol(symbol))              # 55 = symbol, e.g. EUR/USD
    msg.addGroup(group)
    return msg


def process_market_data_snapshot(message, message_time=0, hardcoded_provider=None):
    """Turn a MarketDataSnapshot message into quotes"""
    fix_md_entry = pxm44.MarketDataSnapshotFullRefresh.NoMDEntries()
    # use SendingTime if present
    if message.getHeader().isSetField(52):
        exch_time = sending_time_to_timestamp(message.getHeader().getField(52))
    else:
        exch_time = message_time

    symbol = drop_slash(message.getField(55))    # Symbol
    # snapshot has separate entries for bid/ask, but quotes do not
    entries = {}
    for i in range(int(message.getField(268))):
        message.getGroup(1+i, fix_md_entry)

        entry_id = fix_md_entry.getField(299)           # QuoteEntryID
        entry_type = fix_md_entry.getField(269)         # MDEntryType
        entry_px = float(fix_md_entry.getField(270))    # MDEntryPx
        entry_size = float(fix_md_entry.getField(271))  # MDEntrySize
        if fix_md_entry.isSetField(106):                # Issuer
            provider = fix_md_entry.getField(106)
        else:
            provider = hardcoded_provider

        quote_entry = entries.get(entry_id)
        if quote_entry is None:
            quote_entry = [entry_id, None, None, None, None, None, None]
        if entry_type == '0':  # bid
            quote_entry[1] = entry_size
            quote_entry[3] = entry_px
            quote_entry[5] = provider
        else:
            quote_entry[2] = entry_size
            quote_entry[4] = entry_px
            quote_entry[6] = provider
        entries[entry_id] = quote_entry
    items = list(entries.values())
    return (exch_time, symbol, items, True)


def process_quote_set(quote_set, quote_entry, hardcoded_provider=None):
    entries = []
    # iterate over each quote entry
    for j in range(int(quote_set.getField(295))):
        # copy group into quote_entry
        quote_set.getGroup(1+j, quote_entry)
        # pull out entry data
        entry_id = quote_entry.getField(299)  # die if id is not set
        bid_size = float(quote_entry.getField(134)) if quote_entry.isSetField(134) else None
        ask_size = float(quote_entry.getField(135)) if quote_entry.isSetField(135) else None
        bid_price = float(quote_entry.getField(188)) if quote_entry.isSetField(188) else None
        ask_price = float(quote_entry.getField(190)) if quote_entry.isSetField(190) else None
        if hardcoded_provider:
            bid_provider = ask_provider = hardcoded_provider
        else:
            provider = quote_entry.getField(106) if quote_entry.isSetField(106) else None
            bid_provider = provider if (ask_price is None or bid_size is not None) else None
            ask_provider = provider if (ask_price is not None) else None
        entries.append([
            entry_id,
            bid_size, ask_size,
            bid_price, ask_price,
            bid_provider, ask_provider
        ])
    return entries


def process_mass_quote(message, active_subscriptions, message_time=0, offline=False,
                       hardcoded_provider=None):
    res = []
    quote_set = pxm44.MassQuote.NoQuoteSets()
    quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
    if message.getHeader().isSetField(52):
        exch_time = sending_time_to_timestamp(message.getHeader().getField(52))
    else:
        exch_time = message_time
    # iterate over each quote set
    for i in range(int(message.getField(296))):
        message.getGroup(1+i, quote_set)
        quote_set_id = quote_set.getField(302)  # QuoteSetID
        if offline:
            symbol = drop_slash(quote_set_id)
        else:
            symbol = active_subscriptions.get(quote_set_id)

        if symbol:
            entries = process_quote_set(quote_set, quote_entry,
                                        hardcoded_provider=hardcoded_provider)
            res.append((exch_time, symbol, entries, False))
        else:
            # how to handle this better? throw exception?
            logger.error('%s not found in active_subscriptions', quote_set_id)
    return res


def clear_book(symbol):
    return (-1, symbol, [], True)


# utils
def soh_to_pipe(message):
    return message.toString().replace('\x01', '|')


def drop_slash(symbol):
    return symbol.replace('/', '')


def sending_time_to_timestamp(sending_time):
    """Convert a FIX datetime to unix datetime"""
    strp_format = '%Y%m%d-%H:%M:%S.%f' if len(sending_time) > 17 else '%Y%m%d-%H:%M:%S'
    return int(1e6*datetime.datetime.strptime(sending_time, strp_format)
               .replace(tzinfo=datetime.timezone.utc)
               .timestamp())


def log_time_to_timestamp(log_time):
    """Convert a log datetime to unix datetime"""
    return int(1e6*datetime.datetime.strptime(log_time, '%Y-%m-%d %H:%M:%S.%f')
               .replace(tzinfo=datetime.timezone.utc)
               .timestamp())
