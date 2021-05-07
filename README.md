# Price Feed

## Overview

There are 3 components that make up this service:

  - Price Feed; this is the FIX adapter that will connect out to the provider and process inbound price updates
  - Book Builder; this will take normalised quote updates and create 'book' entries
  - File Writer; this will take the book entries and write them to disk

## Quickstart

Build
```
docker build . -t pricefeed # takes a while to build quickfix wheels
```

Run
```
mkdir -p logs
docker run --rm -ti -v $(pwd)/config:/app/config -v $(pwd)/logs:/app/logs -v $(pwd)/data:/app/data -p 8080:8080 pricefeed
```


### Offline:

**Arguments:**
- `--indir`; directory containing FIX logs to be parsed
- `--infiles`; file or list of files to be parsed (mutually exclusive to --indir)
- `--outdir`; destination for book to be written to, defaults to `./data`
- `--workdir`; working directory, temporary files are put here, defaults to `./work`
- `--log-suffix`; file suffix to filter `--indir` files on, defaults to `.log`
- `--max-levels`; maximum book levels, defaults to 10
- `--cache-size`; filewriter cache - only write to disk once cache is full
- `--block-size`; hdf5 block size (larger size means less resizing, but more wasted space at end of the file)
- `--clear-book-state`; TODO: clear historic book state (e.g. when parsing hours/days not weeks)
- `--debug`; enable debug log level

#### Other

**Run offline for single date**
```sh
# spin up container
docker run --rm -ti -v $(pwd):/app -v /data/price_logs/today/tradefeedr_provider/pricing:/ziplogs --entrypoint /bin/bash pricefeed:latest
# run for 2021.05.02
ZIPDIR=/ziplogs DATE=20210502 sh scripts/run.sh
```

**Create BBO from H5**
``
for f in data/2021-04-04/*.h5; do python3 scripts/h5_to_csv.py $f data/csv/2021-04-04/; done
```
