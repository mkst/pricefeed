import logging
import time

import quickfix as fix
import quickfix44 as fix44

import app.pricefeed as pf

logger = logging.getLogger(__name__)


class FixPriceFeed(fix.Application):
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
        logger.debug('Received: %s', pf.soh_to_pipe(message))
        msg_type = message.getHeader().getField(fix.MsgType()).getString()
        handler = self.handlers.get(msg_type)
        if handler:
            handler(message, session_id)
        else:
            raise Exception('Unsupported MsgType received %s, %s' %
                            (msg_type, pf.soh_to_pipe(message)))

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
        logger.debug('Full Snapshot: %s', pf.soh_to_pipe(message))
        quotes = pf.process_market_data_snapshot(message)
        self.queue.put(quotes)

    def on_mass_quote(self, message, session_id):
        """Turn a MassQuote message into quotes"""
        quotes = pf.process_mass_quote(message, self.active_subscriptions)
        # sadly there's no .put(*quotes)
        for quote in quotes:
            self.queue.put(quote)

        if message.isSetField(fix.QuoteID()):
            self.send_ack(message, session_id)

    # outbound message handlers
    def send_subscriptions(self, session_id):
        """Send MarketDataRequest for all subscriptions"""
        for i, symbol in enumerate(self.subscriptions):
            logging.info('Subscribing to %s (%i)', symbol, i)
            self.active_subscriptions[str(i)] = pf.drop_slash(symbol)
            msg = pf.create_market_data_request(str(i), symbol)
            fix.Session.sendToTarget(msg, session_id)

    # pylint: disable=R0201
    def send_ack(self, message, session_id):
        """Send MassQuoteAck with QuoteID from original MassQuote"""
        quote_id = message.getField(117)
        msg = fix44.MassQuoteAcknowledgement()
        msg.setField(fix.QuoteID(quote_id))  # echo QuoteID back
        logger.debug('Acking message with QuoteID %s', quote_id)
        fix.Session.sendToTarget(msg, session_id)
