import argparse
import datetime
import sys


def zips_for_date(date, suffix='_quote.zip'):
    # generates 0100 -> 0000
    dates = [date + datetime.timedelta(hours=hour) for hour in range(1, 25)]
    dates_string = [d.strftime(f'%Y%m%d-%H%M{suffix}') for d in dates]
    return dates_string


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('date', type=str,
                        help='input date to generate zips for (YYYYMMDD format)')
    parser.add_argument('--date-format', type=str,
                        help='input date format', default='%Y%m%d')
    parser.add_argument('--file-suffix', type=str,
                        help='output file suffix', default='_quote.zip')
    args = parser.parse_args()
    try:
        date = datetime.datetime.strptime(args.date, args.date_format)
    except Exception:
        print('Failed to parse input date %s with format %s' % (args.date, args.date_format))
        return 1
    zips = zips_for_date(date, suffix=args.file_suffix)
    print(" ".join(zips))
    return 0


if __name__ == '__main__':
    res = main()
    sys.exit(res)
