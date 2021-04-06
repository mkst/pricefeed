import unittest
from unittest.mock import MagicMock, Mock, patch

from queue import Empty

import numpy as np

import app.filewriter as fw


class TestFileWriterClass(unittest.TestCase):
    def setUp(self):
        self.inbound_queue = Mock()
        self.inbound_queue.qsize = Mock(side_effect=[1])
        self.shutdown_event = Mock()
        self.file_path = '/dev/shm/test'
        self.cache_size = 2
        self.block_size = 6

        self.item = np.array(np.zeros(1), dtype=[('a', 'float64'), ('b', 'float64'), ('c', 'float64')])
        with patch('os.path.isdir', side_effect=[True]) as _:
            self.filewriter = fw.FileWriter(self.inbound_queue,
                                            self.shutdown_event,
                                            self.cache_size,
                                            self.block_size,
                                            file_path=self.file_path)

    def test_init(self):
        with patch('os.path.isdir', side_effect=[False]) as is_dir:
            with patch('os.makedirs') as makedirs:
                filewriter = fw.FileWriter(self.inbound_queue,
                                           self.shutdown_event,
                                           self.cache_size,
                                           self.block_size,
                                           file_path=self.file_path)
                self.assertEqual(self.inbound_queue, filewriter.inbound_queue)
                self.assertEqual(self.shutdown_event, filewriter.shutdown_event)
                self.assertEqual(self.file_path + '/', filewriter.file_path)
                self.assertEqual(self.cache_size, filewriter.max_cache_size)
                self.assertEqual(self.block_size, filewriter.file_block_size)
                is_dir.assert_called_once()
                makedirs.assert_called_once()

# run
    def test_run(self):
        self.shutdown_event.is_set = Mock(side_effect=[False, True])
        self.inbound_queue.get = Mock(side_effect=["item"])
        with patch('app.filewriter.FileWriter.process_item') as process_item:
            with patch('app.filewriter.FileWriter.shutdown') as shutdown:
                self.filewriter.run()
                process_item.assert_called_once()
                shutdown.assert_called_once()
                self.assertEqual("item", process_item.call_args[0][0])

    def test_run_empty_queue(self):
        self.shutdown_event.is_set = Mock(side_effect=[False, True])
        self.inbound_queue.get = Mock(side_effect=Empty)
        with patch('app.filewriter.FileWriter.process_item') as process_item:
            with patch('app.filewriter.FileWriter.shutdown') as shutdown:
                self.filewriter.run()
                process_item.assert_not_called()
                shutdown.assert_called_once()

# shutdown
    def test_shutdown(self):
        # fake 1 item still on the queue
        self.inbound_queue.get = Mock(side_effect=["item", Empty])
        with patch('app.filewriter.FileWriter.process_item') as process_item:
            with patch('app.filewriter.FileWriter.flush_cache_all') as flush_cache_all:
                self.filewriter.shutdown()
                process_item.assert_called_once()
                self.assertEqual("item", process_item.call_args[0][0])
                self.inbound_queue.close.assert_called_once()
                self.inbound_queue.join_thread.assert_called_once()
                flush_cache_all.assert_called_once()

# process_item
    def test_process_item(self):
        self.filewriter.process_item((1, 'key', self.item))
        self.assertEqual(self.item, self.filewriter.cache.get('key'))

    def test_process_item_flush_cache(self):
        with patch('app.filewriter.flush_cache') as flush_cache:
            self.filewriter.process_item((1, 'key', self.item))
            flush_cache.assert_not_called()
            # max cache size is 2
            self.filewriter.process_item((2, 'key', self.item))
            flush_cache.assert_called_once()
            cache, filename, offset = flush_cache.call_args[0]
            # check arguments
            self.assertSequenceEqual(list(np.concatenate((self.item, self.item))), list(cache))
            self.assertEqual(self.file_path + '/1970-01-01/key.h5', filename)
            self.assertEqual(None, offset)
            # cache empty
            self.assertEqual(None, self.filewriter.cache.get('key'))

    def test_process_item_new_date(self):
        with patch('app.filewriter.FileWriter.flush_cache_all') as flush_cache_all:
            self.filewriter.process_item((86400000000, 'key', self.item))
            flush_cache_all.assert_called_once()
            self.assertEqual('1970-01-02', str(self.filewriter.file_date))

    def test_process_item_same_date(self):
        with patch('app.filewriter.FileWriter.flush_cache_all') as flush_cache_all:
            self.filewriter.process_item((86399999999, 'key', self.item))
            flush_cache_all.assert_not_called()
            self.assertEqual('1970-01-01', str(self.filewriter.file_date))

# flush_cache_all
    def test_flush_cache_all(self):
        with patch('app.filewriter.flush_cache') as flush_cache:
            self.filewriter.process_item((1, 'key', self.item))
            flush_cache.assert_not_called()
            self.filewriter.process_item((2, 'key2', self.item))
            flush_cache.assert_not_called()
            self.filewriter.flush_cache_all()
            self.assertEqual(2, len(flush_cache.call_args_list))
            self.assertEqual(None, self.filewriter.cache['key'])
            self.assertEqual(None, self.filewriter.cache['key2'])
            self.assertEqual(None, self.filewriter.file_offset['key'])
            self.assertEqual(None, self.filewriter.file_offset['key2'])

# get_filename
    def test_get_filename(self):
        self.assertEqual(self.file_path + '/1970-01-01/key.h5',
                         self.filewriter.get_filename('key'))


class TestFileWriterFunctions(unittest.TestCase):

    def setUp(self):
        self.entry = np.array(np.zeros(1), dtype=[('a', 'float64'), ('b', 'float64'), ('c', 'float64')])

# flush_cache
    def test_flush_no_offset_new_file(self):
        with patch('os.path.exists', side_effect=[False]) as _:
            with patch('app.filewriter.write_to_new_dataset_file') as write_to_new_dataset_file:
                fw.flush_cache(None,
                               'filename',
                               None)
                write_to_new_dataset_file.assert_called_once()
                dataset, filename, _ = write_to_new_dataset_file.call_args[0]
                self.assertEqual(None, dataset)
                self.assertEqual('filename', filename)

    def test_flush_no_offset_existing_file(self):
        with patch('os.path.exists', side_effect=[True]) as _:
            with patch('app.filewriter.get_file_offset', side_effect=[123]) as get_file_offset:
                with patch('app.filewriter.write_to_existing_dataset_file') as write_to_existing_dataset_file:
                    fw.flush_cache(None,
                                   'filename',
                                   None)
                    get_file_offset.assert_called_once()
                    filename, _ = get_file_offset.call_args[0]
                    self.assertEqual('filename', filename)
                    write_to_existing_dataset_file.assert_called_once()
                    dataset, filename, offset, _ = write_to_existing_dataset_file.call_args[0]
                    self.assertEqual(None, dataset)
                    self.assertEqual('filename', filename)
                    self.assertEqual(123, offset)

    def test_flush_offset(self):
        with patch('app.filewriter.write_to_existing_dataset_file') as write_to_existing_dataset_file:
            fw.flush_cache(None,
                           'filename',
                           123)
            write_to_existing_dataset_file.assert_called_once()
            dataset, filename, offset, _ = write_to_existing_dataset_file.call_args[0]
            self.assertEqual(None, dataset)
            self.assertEqual('filename', filename)
            self.assertEqual(123, offset)

# write_to_new_dataset_file
    def test_write_to_new_dataset_file(self):
        with patch('h5py.File') as _:
            with patch('os.makedirs') as _:
                res = fw.write_to_new_dataset_file(self.entry, '/dummy/path/filename')
                self.assertEqual(1, res)

# write_to_existing_dataset_file
    def test_write_to_existing_dataset_file(self):
        mock_column = MagicMock()
        mock_column.len = Mock(return_value=4)
        mock_dataset_file = lambda x: {
            'time': mock_column,
            'a': mock_column,
            'b': mock_column,
            'c': mock_column,
        }
        with patch('h5py.File') as mock:
            mock.return_value.__enter__ = mock_dataset_file
            res = fw.write_to_existing_dataset_file(self.entry, 'filename', 2)
            self.assertEqual(3, res)
            mock_column.resize.assert_not_called()

    def test_write_to_existing_dataset_file_needs_resizing(self):
        mock_column = MagicMock()
        mock_column.len = Mock(return_value=4)
        mock_dataset_file = lambda x: {
            'time': mock_column,
            'a': mock_column,
            'b': mock_column,
            'c': mock_column,
        }
        with patch('h5py.File') as mock:
            mock.return_value.__enter__ = mock_dataset_file
            res = fw.write_to_existing_dataset_file(self.entry, 'filename', 3, 10)
            self.assertEqual(4, res)
            new_size, _ = mock_column.resize.call_args
            self.assertEqual((14,), new_size)

# add_cache_entry
    def test_add_cache_entry_no_entries(self):
        res = fw.add_cache_entry(None, self.entry)
        self.assertEqual(1, len(res))

    def test_add_cache_entry_single_entry(self):
        res = fw.add_cache_entry(self.entry, self.entry)
        self.assertEqual(2, len(res))

    def test_add_cache_entry_multiple_entries(self):
        res = fw.add_cache_entry(np.concatenate((self.entry, self.entry, self.entry)), self.entry)
        self.assertEqual(4, len(res))

# get_file_offset
    def test_get_file_offset(self):
        mock_dataset_file = lambda x: {'time': np.array([1, 2, 3, 4, 0, 0, 0, 0])}
        with patch('h5py.File') as mock:
            mock.return_value.__enter__ = mock_dataset_file
            res = fw.get_file_offset('filename', 'time')
            self.assertEqual(4, res)

    def test_get_file_offset_empty(self):
        mock_dataset_file = lambda x: {'time': np.array([0, 0, 0, 0, 0, 0, 0, 0])}

        with patch('h5py.File') as mock:
            mock.return_value.__enter__ = mock_dataset_file
            res = fw.get_file_offset('filename', 'time')
            self.assertEqual(0, res)
