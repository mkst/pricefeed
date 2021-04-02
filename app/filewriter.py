"""Simple File Writer, writes data to disk in hdf5 format"""
import logging
import os
from queue import Empty
import datetime

import h5py
import numpy as np

logger = logging.getLogger(__name__)


class FileWriter():
    # pylint: disable=R0913
    def __init__(self,
                 inbound_queue,
                 shutdown_event,
                 cache_size=1024,
                 block_size=32768,
                 file_path='/dev/shm/book/'
                 ):
        logger.info('Initialising File Writer')
        # sanity
        assert block_size % cache_size == 0
        # queues
        self.inbound_queue = inbound_queue
        # events
        self.shutdown_event = shutdown_event
        # file settings
        if file_path[-1] != '/':
            file_path += '/'  # ensure we create a directory
        self.file_path = file_path
        if not os.path.isdir(self.file_path):
            logger.info('Creating %s', self.file_path)
            os.makedirs(self.file_path)
        self.file_offset = {}
        self.file_date = datetime.date(1970, 1, 1)  # as good as any
        # cache and configuration
        self.cache = {}
        self.file_block_size = block_size
        self.max_cache_size = cache_size

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
        qsize = self.inbound_queue.qsize()
        if qsize > 0:
            logger.warning("Queue contains %i items, consuming before shutting down...", qsize)
        processed = 0
        # drain queue
        while True:
            try:
                # book builder is slower than filewriter, so block during queue drain!
                item = self.inbound_queue.get(block=True, timeout=3)
                processed += 1
            except Empty:
                break
            self.process_item(item)
        if qsize > 0:
            logger.warning("Finished draining queue, processed %i items", processed)
        # clean up
        self.inbound_queue.close()
        self.inbound_queue.join_thread()
        # complete writedown
        self.flush_cache_all()
        logger.info('Shutdown complete!')

    def process_item(self, item):
        """Update cache and write to disk when full"""
        time, key, entry = item
        book_date = datetime.datetime.utcfromtimestamp(time / 1000000).date()
        if book_date > self.file_date:
            # flush all caches
            self.flush_cache_all()
            # update file date
            self.file_date = book_date

        # update cache
        cache = add_cache_entry(self.cache.get(key), entry)
        if cache.size == self.max_cache_size:
            filename = self.get_filename(key)
            offset = self.file_offset.get(key)
            # flush to disk
            new_offset = flush_cache(cache, filename, offset)
            # update offset
            self.file_offset[key] = new_offset
            self.cache[key] = None
        else:
            self.cache[key] = cache

    def flush_cache_all(self):
        for key, cache in self.cache.items():
            if cache is not None:
                logger.info('Flushing %s, %i', key, len(cache))
                filename = self.get_filename(key)
                offset = self.file_offset.get(key)
                flush_cache(cache, filename, offset, self.file_block_size)
                self.cache[key] = None
            # reset file offset
            self.file_offset[key] = None

    def get_filename(self, symbol):
        """Helper function to generate hdf5 filename"""
        # add date, provider?
        return self.file_path + str(self.file_date) + '/' + symbol + '.h5'


def flush_cache(cache, filename, offset, file_block_size=32758):
    """Writes cache to filename at offset, if filename does not exist, then it
    will be created. If offset is None it will be determined from the file."""
    if offset is None:
        if not os.path.exists(filename):
            # write new file and return
            return write_to_new_dataset_file(cache, filename, file_block_size)
        # otherwise determine offset from 'time' column
        offset = get_file_offset(filename, 'time')
        logger.debug("File offset is %i for %s", offset, filename)
    return write_to_existing_dataset_file(cache, filename, offset, file_block_size)


def write_to_new_dataset_file(dataset, filename, initial_block_size=32768):
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        logger.debug('Creating directory %s', dirname)
        os.makedirs(dirname)

    logger.info('Initialising new dataset %s', filename)
    with h5py.File(filename, 'w') as dataset_file:
        for name in dataset.dtype.names:
            dataset_file.create_dataset(name,
                                        data=dataset[name],
                                        chunks=True,       # can only resize if chunked
                                        maxshape=(None,))  # can only resize if no max size
            # initialise first block
            dataset_file[name].resize(initial_block_size, axis=0)
    return dataset.size


def write_to_existing_dataset_file(dataset, filename, offset, file_block_size=32768):
    # sanity check
    assert offset is not None
    # store variable as we use it a few times
    dataset_length = dataset.size
    logger.debug('Writing %i entries to %s', dataset_length, filename)
    with h5py.File(filename, 'a') as dataset_file:
        need_resize = (offset + dataset_length) >= dataset_file['time'].len()
        for name in dataset.dtype.names:
            if need_resize:
                dataset_file[name].resize(file_block_size + dataset_file[name].len(),
                                          axis=0)
            dataset_file[name][offset:offset+dataset_length] = dataset[name]
    return offset + dataset_length


def add_cache_entry(cache, entry):
    if cache is None:
        return entry
    return np.concatenate((cache, entry))


def get_file_offset(filename, column='time'):
    logger.debug('Calculating offset for %s using %s', filename, column)
    # we should not have gaps or zeros in time column.
    with h5py.File(filename, 'r') as dataset_file:
        return len(np.asarray(dataset_file[column]).nonzero()[0])
