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
