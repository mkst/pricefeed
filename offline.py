import argparse
import logging
import os
import signal

from multiprocessing import Event, Process, Queue

import app.offlinepricefeed as offlinepricefeed
import app.bookbuilder as bookbuilder
import app.filewriter as filewriter


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
                        consumer_shutdown_event, config, max_levels):
    """Wrapper for turning bookbuilder into a multiprocessing.Process"""
    book_builder = bookbuilder.BookBuilder(inbound_queue,
                                           outbound_queue,
                                           shutdown_event,
                                           consumer_shutdown_event,
                                           config,
                                           max_levels)
    book_builder.run()


def create_price_feed(outbound_queue,
                      shutdown_event,
                      config,
                      infiles,
                      hardcoded_provider,
                      safe_mode):
    ofp = offlinepricefeed.OfflinePriceFeed(outbound_queue,
                                            shutdown_event,
                                            config,
                                            infiles,
                                            hardcoded_provider,
                                            safe_mode)
    ofp.run()


def get_files_from_directory(indir, suffix='.log'):
    files = os.listdir(indir)
    files = filter(lambda x: x.endswith(suffix), files)
    return [open(os.path.join(indir, f), 'r') for f in files]


def main():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--indir', type=str,
                       help='path containing FIX logs to be parsed')
    group.add_argument('--infiles', type=argparse.FileType('r'), nargs='+',
                       help='input file(s) to be parsed')

    parser.add_argument('--log-suffix', type=str, default='.log',
                        help='input file suffix (default: .log)')
    parser.add_argument('--outdir', type=str, default='data',
                        help='path to write data to')
    parser.add_argument('--workdir', type=str, default='work',
                        help='explicit path for working directory (default: ./work)')
    # book builder
    parser.add_argument('--max-levels', type=int,
                        help='maximum book depth to write to (default: 10)', default=10)
    parser.add_argument('--cache-size', type=int,
                        help='filewriter cache size (default: 1024)', default=1024)
    parser.add_argument('--block-size', type=int,
                        help='filewriter on-disk block size (default: 1024)', default=1024)
    parser.add_argument('--clear-book', action='store_true', default=False)
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--hardcoded-provider', type=str,
                        help='force provider id, e.g. 0', default=None)
    parser.add_argument('--safe-mode', action='store_true', default=False)

    args = parser.parse_args()

    if args.indir:
        infiles = get_files_from_directory(args.indir, args.log_suffix)
    else:
        infiles = args.infiles

    config = {
        'mappings_path': os.path.join(args.workdir, 'mappings.json'),
        'clear_book': args.clear_book,
        'book_path': os.path.join(args.workdir, 'book.json'),
    }

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(handlers=[logging.StreamHandler()],
                        level=loglevel,
                        format=('%(asctime)s.%(msecs)03d %(levelname)s %(filename)s ' +
                                '%(funcName)s %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S')

    for key, value in config.items():
        logging.info('CONFIG: %s is %r', key, value)

    # prevent child processes from receiving CTRL+C
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

    shutdown_event = Event()
    consumer_shutdown_event = Event()
    fix_outbound_queue = Queue()
    bb_outbound_queue = Queue()

    # create our processes
    consumer = Process(name='filewriter',
                       target=create_file_writer,
                       args=(bb_outbound_queue, consumer_shutdown_event,
                             args.cache_size,
                             args.block_size,
                             args.outdir))
    producer_consumer = Process(name='bookbuilder',
                                target=create_book_builder,
                                args=(fix_outbound_queue, bb_outbound_queue,
                                      shutdown_event, consumer_shutdown_event,
                                      config, args.max_levels))
    producer = Process(name='pricefeed',
                       target=create_price_feed,
                       args=(fix_outbound_queue, shutdown_event,
                             config,
                             infiles,
                             args.hardcoded_provider,
                             args.safe_mode))

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
            logging.info("producer joined")
            producer_consumer.join()
            logging.info("producer_consumer joined")
            consumer.join()
            logging.info("consumer joined")
        except KeyboardInterrupt:
            logging.warning('CTRL+C received, shutting down')
            shutdown_event.set()


if __name__ == '__main__':
    main()
