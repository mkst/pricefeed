import datetime
import os
import sys

import quickfix as fix

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app.pricefeed
import app.pxm44 as pxm44

DATA_DICTIONARY = fix.DataDictionary()
DATA_DICTIONARY.readFromURL('spec/pxm44.xml')
# 20 level book
MSG = fix.Message('8=FIX.4.4|9=1299|35=i|34=1113826|49=XCT|52=20171106-14:57:08.528|56=Q001|296=1|302=1|295=20|299=0|106=1|134=100000|135=100000|188=1.80699|190=1.80709|299=1|106=1|134=250000|135=250000|188=1.80698|190=1.80710|299=2|106=1|134=500000|135=500000|188=1.80697|190=1.80711|299=3|106=1|134=750000|135=750000|188=1.80695|190=1.80712|299=4|106=1|134=1000000|135=1000000|188=1.80694|190=1.80713|299=5|106=1|134=2000000|135=2000000|188=1.80693|190=1.80714|299=6|106=1|134=3000000|135=3000000|188=1.80692|190=1.80715|299=7|106=1|134=5000000|135=5000000|188=1.80691|190=1.80716|299=8|106=1|134=7500000|135=7500000|188=1.80690|190=1.80717|299=9|106=1|134=10000000|135=10000000|188=1.80689|190=1.80718|299=10|106=1|134=15000000|135=15000000|188=1.80688|190=1.80719|299=11|106=1|134=20000000|135=20000000|188=1.80687|190=1.80720|299=12|106=1|134=30000000|135=30000000|188=1.80686|190=1.80721|299=13|106=1|134=40000000|135=40000000|188=1.80685|190=1.80722|299=14|106=1|134=50000000|135=50000000|188=1.80684|190=1.80723|299=15|106=1|134=60000000|135=60000000|188=1.80683|190=1.80724|299=16|106=1|134=70000000|135=70000000|188=1.80682|190=1.80725|299=17|106=1|134=80000000|135=80000000|188=1.80681|190=1.80726|299=18|106=1|134=90000000|135=90000000|188=1.80680|190=1.80727|299=19|106=1|134=10000000|135=10000000|188=1.80679|190=1.80728|10=209|'.replace('|', '\x01'), DATA_DICTIONARY)


def bench_process_mass_quote(iterations):
    subs = {'1': 'EURUSD'}
    start_time = datetime.datetime.now()
    for _ in range(iterations):
        app.pricefeed.process_mass_quote(MSG, subs)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    return ('process_mass_quote', iterations, duration)

def bench_process_quote_set(iterations):
    quote_set = pxm44.MassQuote.NoQuoteSets()
    quote_entry = pxm44.MassQuote.NoQuoteSets.NoQuoteEntries()
    MSG.getGroup(1, quote_set)
    start_time = datetime.datetime.now()
    for _ in range(iterations):
        app.pricefeed.process_quote_set(quote_set, quote_entry)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    return ('process_quote_set', iterations, duration)


def print_results(func, iterations, duration):
    print(','.join([
        func,
        str(iterations),
        str(duration),
        '%f' % (duration / iterations)
        ]))


def main():
    print('function,iterations,total,iteration')
    # res = bench_process_quote_set(100000)
    res = bench_process_mass_quote(100000)
    print_results(*res)


if __name__ == '__main__':
    main()

# function,iterations,total,iteration
# process_quote_set,100000,22.834905,0.000228
