"""FIX Price Feed for PrimeXM 4.4"""

import argparse
import logging
import signal

from multiprocessing import Event, Process, Queue

import quickfix as fix

from app import bookbuilder, filewriter, pricefeed


def create_file_writer(inbound_queue, shutdown_event, cache_size, block_size, file_path):
    """Wrapper for turning bookbuilder into a multiprocessing.Process"""
    file_writer = filewriter.FileWriter(inbound_queue,
                                        shutdown_event,
                                        cache_size=cache_size,
                                        block_size=block_size,
                                        file_path=file_path
                                        )
    file_writer.run()


def create_book_builder(inbound_queue, outbound_queue, shutdown_event,
                        consumer_shutdown_event, max_levels):
    """Wrapper for turning bookbuilder into a multiprocessing.Process"""
    book_builder = bookbuilder.BookBuilder(inbound_queue,
                                           outbound_queue,
                                           shutdown_event,
                                           consumer_shutdown_event,
                                           max_levels)
    book_builder.run()


def create_fix_client(outbound_queue, shutdown_event, subscriptions, cfg):
    """Wrapper for turning pricefeed into a multiprocessing.Process"""
    try:
        settings = fix.SessionSettings(cfg)
        store_factory = fix.FileStoreFactory(settings)
        log_factory = fix.FileLogFactory(settings)
        feed = pricefeed.PriceFeed(outbound_queue, shutdown_event, subscriptions)
        initiator = fix.SocketInitiator(feed, store_factory, settings, log_factory)
        feed.set_fix_adapter(initiator)
        feed.run()
    except fix.ConfigError as exception:
        shutdown_event.set()
        logging.error(exception)


def main():
    """The main event"""

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str,
                        help='quickfix configuration file')
    parser.add_argument('subscriptions', type=argparse.FileType('r'),
                        help='subscriptions configuration file')
    parser.add_argument('filepath', type=str,
                        help='path to write data to')
    parser.add_argument('--max-levels', type=int,
                        help='maximum book depth to write to (default: 10)', default=10)
    parser.add_argument('--cache-size', type=int,
                        help='filewriter cache size (default: 1024)', default=1024)
    parser.add_argument('--block-size', type=int,
                        help='filewriter on-disk block size (default: 32768)', default=32768)
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.INFO

    # setup logging
    logging.basicConfig(handlers=[logging.StreamHandler()],
                        level=loglevel,
                        format=('%(asctime)s.%(msecs)03d %(levelname)s %(filename)s ' +
                                '%(funcName)s %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S')

    # get from subscriptions.txt
    subscriptions_file = args.subscriptions
    subscriptions = []
    for line in subscriptions_file.readlines():
        subscriptions.append(line.strip())
    subscriptions_file.close()

    # prevent child processes from receiving CTRL+C
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

    # create SHUTDOWN event
    shutdown_event = Event()
    consumer_shutdown_event = Event()
    # create queue for message flow from fix broker => book builder
    fix_outbound_queue = Queue()
    # create queue for message flow from book builder => file writer
    bb_outbound_queue = Queue()
    # create our processes
    consumer = Process(name='filewriter',
                       target=create_file_writer,
                       args=(bb_outbound_queue, consumer_shutdown_event,
                             args.cache_size,
                             args.block_size,
                             args.filepath))
    producer_consumer = Process(name='bookbuilder',
                                target=create_book_builder,
                                args=(fix_outbound_queue, bb_outbound_queue,
                                      shutdown_event, consumer_shutdown_event,
                                      args.max_levels))
    producer = Process(name='pricefeed',
                       target=create_fix_client,
                       args=(fix_outbound_queue, shutdown_event,
                             subscriptions, args.config))
    # spin up
    consumer.start()
    producer_consumer.start()
    producer.start()

    # re-set sigint
    signal.signal(signal.SIGINT, original_sigint_handler)

    while not shutdown_event.is_set():
        try:
            # wait for them to finish
            producer.join()
            producer_consumer.join()
            consumer.join()
        except KeyboardInterrupt:
            logging.warning('CTRL+C received, shutting down')
            shutdown_event.set()


if __name__ == '__main__':
    main()
