import datetime
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app.bookbuilder


ITEM = (1509980228528000, 'EURDKK', [
    ['0', 100000.0, 100000.0, 1.80699, 1.80709, '1'],
    ['1', 250000.0, 250000.0, 1.80698, 1.80710, '1'],
    ['2', 500000.0, 500000.0, 1.80697, 1.80711, '1'],
    ['3', 750000.0, 750000.0, 1.80695, 1.80712, '1'],
    ['4', 1000000.0, 1000000.0, 1.80694, 1.80713, '1'],
    ['5', 2000000.0, 2000000.0, 1.80693, 1.80714, '1'],
    ['6', 3000000.0, 3000000.0, 1.80692, 1.80715, '1'],
    ['7', 5000000.0, 5000000.0, 1.80691, 1.80716, '1'],
    ['8', 7500000.0, 7500000.0, 1.80690, 1.80717, '1'],
    ['9', 10000000.0, 10000000.0, 1.80689, 1.80718, '1'],
    ['10', 15000000.0, 15000000.0, 1.80688, 1.80719, '1'],
    ['11', 20000000.0, 20000000.0, 1.80687, 1.80720, '1'],
    ['12', 30000000.0, 30000000.0, 1.80686, 1.80721, '1'],
    ['13', 40000000.0, 40000000.0, 1.80685, 1.80722, '1'],
    ['14', 50000000.0, 50000000.0, 1.80684, 1.80723, '1'],
    ['15', 60000000.0, 60000000.0, 1.80683, 1.80724, '1'],
    ['16', 70000000.0, 70000000.0, 1.80682, 1.80725, '1'],
    ['17', 80000000.0, 80000000.0, 1.80681, 1.80726, '1'],
    ['18', 90000000.0, 90000000.0, 1.80680, 1.80727, '1'],
    ['19', 10000000.0, 10000000.0, 1.80679, 1.80728, '1']])

QUOTES = [
    {'entry_type': 0, 'price': 1.80699, 'size': 100000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80709, 'size': 100000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80698, 'size': 250000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80710, 'size': 250000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80697, 'size': 500000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80711, 'size': 500000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80695, 'size': 750000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80712, 'size': 750000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80694, 'size': 1000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80713, 'size': 1000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80693, 'size': 2000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80714, 'size': 2000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80692, 'size': 3000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80715, 'size': 3000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80691, 'size': 5000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80716, 'size': 5000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80690, 'size': 7500000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80717, 'size': 7500000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80689, 'size': 10000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80718, 'size': 10000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80688, 'size': 15000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80719, 'size': 15000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80687, 'size': 20000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80720, 'size': 20000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80686, 'size': 30000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80721, 'size': 30000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80685, 'size': 40000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80722, 'size': 40000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80684, 'size': 50000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80723, 'size': 50000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80683, 'size': 60000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80724, 'size': 60000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80682, 'size': 70000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80725, 'size': 70000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80681, 'size': 80000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80726, 'size': 80000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80680, 'size': 90000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80727, 'size': 90000000.0, 'time': 1595336924000000},
    {'entry_type': 0, 'price': 1.80679, 'size': 10000000.0, 'time': 1595336924000000},
    {'entry_type': 1, 'price': 1.80728, 'size': 10000000.0, 'time': 1595336924000000}
    ]


def bench_update_quotes(iterations):
    start_time = datetime.datetime.now()
    time, _, quotes = ITEM
    res = {}
    for _ in range(iterations):
        res = app.bookbuilder.update_quotes(time, res, quotes)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    return ("process_items", iterations, duration)


def bench_build_book(iterations):
    schema = app.bookbuilder.create_schema(10)
    start_time = datetime.datetime.now()
    schema = np.empty(1, dtype=schema)
    for _ in range(iterations):
        app.bookbuilder.build_book(1, QUOTES, schema, 10)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    return ("build_book", iterations, duration)


def bench_flip_quotes(iterations):
    start_time = datetime.datetime.now()
    for _ in range(iterations):
        app.bookbuilder.flip_quotes(QUOTES, 0, False)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    return ("flip_quotes", iterations, duration)


def print_results(func, iterations, duration):
    print(",".join([
        func,
        str(iterations),
        str(duration),
        '%f' % (duration / iterations)
        ]))


def main():
    print("function,iterations,total,iteration")
    res = bench_update_quotes(100000)
    print_results(*res)
    res = bench_build_book(100000)
    print_results(*res)
    res = bench_flip_quotes(100000)
    print_results(*res)


if __name__ == '__main__':
    main()

# function,iterations,total,iteration
# process_items,100000,2.942874,0.000029
# build_book,100000,5.595545,0.000056
# flip_quotes,100000,2.490446,0.000025
