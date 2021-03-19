import logging
import datetime
import time

import quickfix as fix
import quickfix44 as fix44

import app.pxm44 as pxm44

logger = logging.getLogger(__name__)


class PriceFeed(fix.Application):
    def __init__(self, message_queue, shutdown_event, subscriptions):
        logger.info('Initialising Price Feed')
        # internal state
        self.fix_adapter = None
        self.has_ever_logged_on = False
        # arguments
        self.queue = message_queue
        self.shutdown_event = shutdown_event
        self.subscriptions = subscriptions
        self.active_subscriptions = {}
        # message handlers
        self.handlers = {}
        self.handlers[fix.MsgType_MassQuote] = self.on_mass_quote
        self.handlers[fix.MsgType_MarketDataSnapshotFullRefresh] = self.on_market_data_snapshot
        self.handlers[fix.MsgType_MarketDataRequestReject] = self.on_market_data_request_reject
        # group objects
        self.quote_set = pxm44.MassQuote.NoQuoteSets()
        self.quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
        self.md_entry = pxm44.MarketDataSnapshotFullRefresh.NoMDEntries()
        # call parent's init
        super().__init__()

    def set_fix_adapter(self, fix_adapter):
        """Allow PriceFeed to call stop() on the SocketInitiator"""
        self.fix_adapter = fix_adapter

    def run(self):
        self.fix_adapter.start()
        while not self.fix_adapter.isStopped() and not self.shutdown_event.is_set():
            time.sleep(0.1)
        self.shutdown()

    def shutdown(self):
        logger.info('Shutdown triggered!')
        if not self.fix_adapter.isStopped():
            logger.info('Stopping FIX Adapter')
            self.fix_adapter.stop()
        if not self.shutdown_event.is_set():
            logger.info('Triggering shutdown event')
            self.shutdown_event.set()
        logger.info('Shutdown complete!')

    # quickfix core callbacks

    # pylint: disable=R0201,W0613
    def on_create(self, session_id):  # pragma: no cover
        """Notification of a session being created."""
        return

    def on_logon(self, session_id):
        """Notification of a session successfully logging on."""
        logger.debug('Logged ON %s', session_id)
        self.has_ever_logged_on = True
        self.send_subscriptions(session_id)

    def on_logout(self, session_id):
        """Notification of a session logging off or disconnecting."""
        if self.fix_adapter is not None and self.has_ever_logged_on:
            logger.info('Logged OFF %s', session_id)
            self.shutdown()

    def to_admin(self, message, session_id):  # pragma: no cover
        """Notification of admin message being sent to target."""
        if message.getHeader().getField(fix.MsgType()).getString() == 'A':  # LOGON
            session_settings = self.fix_adapter.getSessionSettings(session_id)
            if session_settings.has('Username'):
                message.getHeader().setField(553, session_settings.getString('Username'))
            if session_settings.has('Password'):
                message.getHeader().setField(554, session_settings.getString('Password'))

    # pylint: disable=R0201,W0613
    def to_app(self, message, session_id):  # pragma: no cover
        """Notification of app message being sent to target."""
        return

    # pylint: disable=R0201, W0613
    def from_admin(self, message, session_id):  # pragma: no cover
        """Notification of admin message being received from target."""
        return

    def from_app(self, message, session_id):
        """Notification of app message being received from target."""
        logger.debug('Received: %s', soh_to_pipe(message))
        msg_type = message.getHeader().getField(fix.MsgType()).getString()
        handler = self.handlers.get(msg_type)
        if handler:
            handler(message, session_id)
        else:
            raise Exception('Unsupported MsgType received %s, %s' %
                            (msg_type, soh_to_pipe(message)))

    # aliases to override inherited methods
    onCreate = on_create
    onLogon = on_logon
    onLogout = on_logout
    toAdmin = to_admin
    toApp = to_app
    fromAdmin = from_admin
    fromApp = from_app

    # inbound message handlers

    def on_market_data_request_reject(self, message, session_id):
        """Handle a MarketDataRequestReject message"""
        text = message.getField(58)
        md_req_id = message.getField(fix.MDReqID()).getString()
        logger.warning('Market Data Request with ID %s rejected: %s', md_req_id, text)
        if self.active_subscriptions.get(md_req_id):
            del self.active_subscriptions[md_req_id]

    def on_market_data_snapshot(self, message, session_id):
        """Turn a MarketDataSnapshot message into quotes"""
        logger.debug('Full Snapshot: %s', soh_to_pipe(message))

        exch_time = sending_time_to_timestamp(message.getHeader().getField(52))
        symbol = drop_slash(message.getField(55))    # Symbol
        # snapshot has separate entries for bid/ask, but quotes do not
        entries = {}
        for i in range(int(message.getField(268))):
            message.getGroup(1+i, self.md_entry)

            entry_id = self.md_entry.getField(299)           # QuoteEntryID
            entry_type = self.md_entry.getField(269)         # MDEntryType
            entry_px = float(self.md_entry.getField(270))    # MDEntryPx
            entry_size = float(self.md_entry.getField(271))  # MDEntrySize
            provider = self.md_entry.getField(106)           # Issuer

            quote_entry = entries.get(entry_id)
            if quote_entry is None:
                quote_entry = [entry_id, None, None, None, None, provider]
            if entry_type == '0':  # bid
                quote_entry[1] = entry_size
                quote_entry[3] = entry_px
            else:
                quote_entry[2] = entry_size
                quote_entry[4] = entry_px
            entries[entry_id] = quote_entry
        items = list(entries.values())
        self.queue.put((exch_time, symbol, items, True))

    def on_mass_quote(self, message, session_id):
        """Turn a MassQuote message into quotes"""
        exch_time = sending_time_to_timestamp(message.getHeader().getField(52))
        # iterate over each quote set
        for i in range(int(message.getField(296))):
            message.getGroup(1+i, self.quote_set)
            quote_set_id = self.quote_set.getField(302)
            symbol = self.active_subscriptions.get(quote_set_id)
            if symbol is None:
                logger.error('%s not found in active_subscriptions', quote_set_id)
                return
            entries = process_quote_set(self.quote_set, self.quote_entry)
            self.queue.put((exch_time, symbol, entries, False))

        if message.isSetField(fix.QuoteID()):
            self.send_ack(message, session_id)

    # outbound message handlers
    def send_subscriptions(self, session_id):
        """Send MarketDataRequest for all subscriptions"""
        for i, symbol in enumerate(self.subscriptions):
            logging.info('Subscribing to %s (%i)', symbol, i)
            self.active_subscriptions[str(i)] = drop_slash(symbol)
            msg = create_market_data_request(str(i), symbol)
            fix.Session.sendToTarget(msg, session_id)

    # pylint: disable=R0201
    def send_ack(self, message, session_id):
        """Send MassQuoteAck with QuoteID from original MassQuote"""
        quote_id = message.getField(117)
        msg = fix44.MassQuoteAcknowledgement()
        msg.setField(fix.QuoteID(quote_id))  # echo QuoteID back
        logger.debug('Acking message with QuoteID %s', quote_id)
        fix.Session.sendToTarget(msg, session_id)


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


def process_quote_set(quote_set, quote_entry):
    entries = []
    # iterate over each quote entry
    for j in range(int(quote_set.getField(295))):
        # copy group into quote_entry
        quote_set.getGroup(1+j, quote_entry)
        # pull out entry data
        entry_id = quote_entry.getField(299)  # die if id is not set
        provider = quote_entry.getField(106) if quote_entry.isSetField(106) else None
        bid_size = float(quote_entry.getField(134)) if quote_entry.isSetField(134) else None
        ask_size = float(quote_entry.getField(135)) if quote_entry.isSetField(135) else None
        bid_price = float(quote_entry.getField(188)) if quote_entry.isSetField(188) else None
        ask_price = float(quote_entry.getField(190)) if quote_entry.isSetField(190) else None
        entries.append([entry_id, bid_size, ask_size, bid_price, ask_price, provider])
    return entries
