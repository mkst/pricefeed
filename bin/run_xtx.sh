#!/bin/bash

docker run --rm -v $(pwd):/app \
  -v /data/price_logs/today/quote_collector2/pricing:/zips \
  -e PROVIDER=1 \
  -e WORKDIR=/app/work/xtx \
  -e DATADIR=/app/data/xtx \
  -e CSVDIR=/app/data/xtx/csv \
  -e HDBDIR=/app/hdb/xtx \
  -e ZIPDIR=/zips \
  --entrypoint /bin/sh pricefeed:latest -c 'sh /app/bin/cron.sh'
