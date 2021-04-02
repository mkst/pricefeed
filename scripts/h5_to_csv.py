import argparse
from datetime import datetime
import os
import sys

import vaex


# simply dump out a csv
def dump_book(infile, outfile):
    try:
        df = vaex.open(infile)
    except Exception:
        return 1
    print("Dumping %s to %s" % (infile, outfile))
    df.export(outfile)
    return 0


def dump_bbo(infile, outpath, symbol):
    # column ordering
    columns = ['time', 'sym', 'bid', 'ask', 'mid']
    # load from disk
    try:
        df = vaex.open(infile)
    except Exception:
        return 1
    # blocksize means we may have empty rows at the end, so remove them
    df = df.filter(df.time > 0)
    # only use rows with bid and ask prices
    unfiltered_length = len(df)
    df = df.filter(df.bid_px0 > 0)
    df = df.filter(df.ask_px0 > 0)
    if len(df) != unfiltered_length:
        print("Filtered out %i zero price(s)" % (unfiltered_length - len(df)))
    if len(df) == 0:
        print("No rows for %s" % infile)
        return 0
    # commit filters
    df = df.extract()
    # convert epoch to datetime
    df['time'] /= 1000000
    df['time'] = df['time'].apply(datetime.utcfromtimestamp)
    # add sym in as this data is parted on disk
    df['sym'] = vaex.vrange(0, len(df))
    # FIXME: ugly vaex hack, see https://github.com/vaexio/vaex/issues/802
    df['sym'] = (df['sym'] * 0).astype('str').str.replace('0.0', symbol)
    # create simple mid
    df['mid'] = 0.5 * (df['bid_px0'] + df['ask_px0'])
    # rename columns
    df.rename('bid_px0', 'bid')
    df.rename('ask_px0', 'ask')
    # select out the columns we want
    df = df[columns]
    # write down
    print("Writing down %i entries to %s" % (len(df), outpath))
    df.export_csv(outpath)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=str,
                        help='input file (h5)')
    parser.add_argument('outpath', type=str,
                        help='directory to save output csv')
    parser.add_argument('mode', type=str,
                        help='book or bbo')
    args = parser.parse_args()

    if args.mode not in ('bbo', 'book'):
        print("ERROR mode must be either 'bbo' or 'book'")
        sys.exit(1)

    symbol = os.path.basename(args.infile).split('.')[0]
    outfile = os.path.join(args.outpath, args.mode + symbol + ".csv")
    if args.mode == 'bbo':
        res = dump_bbo(args.infile, outfile, symbol)
    else:
        res = dump_book(args.infile, outfile)

    sys.exit(res)


if __name__ == '__main__':
    main()
