import argparse
from datetime import datetime
import os
import vaex


def dump_bbo(inpath, outpath, symbol):
    # column ordering
    columns = ['time', 'sym', 'bid', 'ask', 'mid']
    # load from disk
    df = vaex.open(inpath)
    # blocksize means we may have empty rows at the end, so remove them
    df = df.filter(df.time > 0)
    # only use rows with bid and ask prices
    unfiltered_length = len(df)
    df = df.filter(df.bid_px0 > 0)
    df = df.filter(df.ask_px0 > 0)
    if len(df) != unfiltered_length:
        print("Filtered out %i zero price(s)" % (unfiltered_length - len(df)))
    if len(df) == 0:
        print("No rows for %s" % inpath)
        return
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inpath', type=str,
                        help='input file to be processed')
    parser.add_argument('outdir', type=str,
                        help='directory to save output csv')
    args = parser.parse_args()

    # construct output filepath
    symbol = os.path.basename(args.inpath).split('.')[0]
    outpath = os.path.join(args.outdir, symbol + ".csv")

    dump_bbo(args.inpath, outpath, symbol)


if __name__ == '__main__':
    main()
