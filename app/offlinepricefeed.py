import datetime
import logging
import json
import os

import quickfix as fix
import quickfix44 as fix44

import app.pricefeed as pf

logger = logging.getLogger(__name__)


class OfflinePriceFeed():

    def __init__(self, queue, shutdown_event, config, file_list=list()):
        logger.info('Initialising Offline Price Feed')
        #
        self.queue = queue
        self.shutdown_event = shutdown_event
        self.config = config
        self.file_list = file_list
        #
        self.data_dictionary = fix.DataDictionary()
        self.data_dictionary.readFromURL('spec/pxm44.xml')
        self.handlers = {}
        self.handlers[fix.MsgType_MassQuote] = self.on_mass_quote
        self.handlers[fix.MsgType_MarketDataSnapshotFullRefresh] = self.on_market_data_snapshot
        self.handlers[fix.MsgType_MarketDataRequestReject] = self.on_market_data_request_reject
        self.handlers[fix.MsgType_MarketDataRequest] = self.on_market_data_request
        # admin
        self.handlers[fix.MsgType_Logon] = self.on_logon
        self.handlers[fix.MsgType_Logout] = self.on_logout
        self.handlers[fix.MsgType_Heartbeat] = self.on_heartbeat
        self.handlers[fix.MsgType_TestRequest] = self.on_testrequest
        self.handlers[fix.MsgType_MassQuoteAcknowledgement] = self.on_mass_quote_ack
        #
        self.active_subscriptions = {}
        # stats
        self.message_count = 0
        self.price_update_count = 0
        # load mappings
        mappings_path = self.config.get('mappings_path')
        if mappings_path and os.path.isfile(mappings_path):
            with open(mappings_path, 'r') as infile:
                self.active_subscriptions = json.load(infile)
                logger.info('Loaded %i subscriptions from %s',
                            len(self.active_subscriptions), mappings_path)
                logger.debug('Subscriptions map: %s', self.active_subscriptions)

    def run(self):
        for file in self.file_list:
            start_time = datetime.datetime.now()
            self.parse_file(file)
            file.close()
            duration = (datetime.datetime.now() - start_time).total_seconds()
            logging.info('Finished parsing %s', file.name)
            logging.info('Processed %i messages (%i price updates) in %i second(s)',
                         self.message_count, self.price_update_count, duration)
            logging.info('Rate: %.2f messages/second)', self.message_count / duration)
            if self.shutdown_event.is_set():
                logging.info('Shutdown detected')
                break
        self.shutdown()

    def shutdown(self):
        logging.info('Shutdown triggered')
        mappings_path = self.config.get('mappings_path')
        if mappings_path:
            with open(mappings_path, 'w') as outfile:
                json.dump(self.active_subscriptions, outfile)
        if not self.shutdown_event.is_set():
            logger.info('Triggering shutdown event')
            self.shutdown_event.set()
        logger.info('Shutdown complete!')

    def to_fix_message(self, line):
        message = fix.Message(line, self.data_dictionary)
        msg_type = message.getHeader().getField(fix.MsgType()).getString()
        return msg_type, message

    def parse_fix_line(self, line):
        try:
            msg_type, message = self.to_fix_message(line)
        except (fix.MessageParseError, fix.InvalidMessage) as e:
            logging.error("Failed to parse %r", e)
            return
        handler = self.handlers.get(msg_type)
        if handler:
            handler(message)
        else:
            logger.warning('Unsupported MsgType received %s %s', msg_type, message)

    def parse_nonfix_line(self, line):
        # add some other handlers here?
        start = line.find('[INFO ]')
        if start > -1:
            logger.info('NON-FIX line: %r', line[start:])
        else:
            logger.warning('NON-FIX line: %r', line)

    def parse_file(self, file):
        logger.info("Parsing %s", file.name)
        for line in file.readlines():
            # remove newlines et al
            line = line.strip()
            start = line.find('8=FIX.4.4')
            if start > -1:
                self.parse_fix_line(line[start:])
                self.message_count += 1
            else:
                self.parse_nonfix_line(line)

    def on_market_data_request(self, message):
        logger.debug('%s', message)
        symbol_group = fix44.MarketDataRequest.NoRelatedSym()
        message.getGroup(1, symbol_group)
        id = message.getField(262)
        symbol = pf.drop_slash(symbol_group.getField(55))
        self.update_subscriptions(id, symbol)
        # clear book
        self.queue.put(pf.clear_book(symbol))

    def on_mass_quote(self, message):
        logger.debug('mass quote %s', message)
        self.price_update_count += 1
        quotes = pf.process_mass_quote(message, self.active_subscriptions)
        # sadly there's no .put(*quotes)
        for quote in quotes:
            self.queue.put(quote)

    def on_market_data_snapshot(self, message):
        logger.debug('snapshot %s', message)
        self.price_update_count += 1
        # snapshots contain symbol<>id mapping, so use it
        id = message.getField(262)
        symbol = pf.drop_slash(message.getField(55))
        if self.update_subscriptions(id, symbol):
            logger.info('Subscription updated from Snapshot')
        # process
        quotes = pf.process_market_data_snapshot(message)
        self.queue.put(quotes)

    def on_logon(self, message):  # pragma: no cover
        logger.info('%s', pf.soh_to_pipe(message))

    def on_logout(self, message):  # pragma: no cover
        logger.info('%s', pf.soh_to_pipe(message))

    def on_heartbeat(self, message):  # pragma: no cover
        logger.debug('%s', message)

    def on_testrequest(self, message):  # pragma: no cover
        logger.debug('%s', message)

    def on_market_data_request_reject(self, message):  # pragma: no cover
        logger.info('%s', pf.soh_to_pipe(message))

    def on_mass_quote_ack(self, message):  # pragma: no cover
        logger.debug('%s', message)

    def update_subscriptions(self, id, symbol):
        current_symbol = self.active_subscriptions.get(id)
        if current_symbol != symbol:
            self.active_subscriptions[id] = symbol
            if current_symbol is None:
                logger.info('Adding Mapping %s => %s', id, symbol)
            else:
                logger.info('Updating Mapping %s => %s (was %s)', id, current_symbol, symbol)
            return True
        return False
