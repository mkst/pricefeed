'''Read in a h5 file, trim and compress'''

import argparse
import logging
import os

import h5py
import numpy as np


def print_stats(infile, outfile):
    infile_stat = os.stat(infile).st_size
    outfile_stat = os.stat(outfile).st_size
    logging.info("%.2f MB => %.2f MB (%.2f%%)",
                 infile_stat / (1024*1024), outfile_stat / (1024*1024),
                 100 * outfile_stat / infile_stat)


def compress_h5_file(infile, outfile, compression='gzip', default_column='time'):
    logging.info("Finalizing %s as %s with %s compression",
                 infile.filename, outfile.filename, compression)
    used = len(np.asarray(infile[default_column]).nonzero()[0])
    logging.info("Dataset contains %i records (%i blocks)", used, infile[default_column].len())
    for column in infile.values():
        logging.debug("Compressing %s...", column.name)
        outfile.create_dataset(column.name,
                               data=infile[column.name][:used],
                               compression=compression,
                               chunks=True,
                               maxshape=(used,))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=str)
    parser.add_argument('outfile', type=str)
    parser.add_argument('--debug', action='store_true', default=False)

    args = parser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(handlers=[logging.StreamHandler()],
                        level=loglevel,
                        format=('%(asctime)s.%(msecs)03d %(levelname)s %(filename)s ' +
                                '%(funcName)s %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S')

    compress_h5_file(h5py.File(args.infile, 'r'), h5py.File(args.outfile, 'w'))
    print_stats(args.infile, args.outfile)


if __name__ == '__main__':
    main()
