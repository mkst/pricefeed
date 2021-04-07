#!/bin/bash

BASE_DIR="$( cd "$( dirname "$0" )/../" &> /dev/null && pwd )"

# default paths
DATADIR="${DATADIR:-${BASE_DIR}/data}"
CSVDIR="${CSVDIR:-${BASE_DIR}/data/csv}"
WORKDIR="${WORKDIR:-${BASE_DIR}/work}"

# process yesterday by default
LOGDATE=$(date --date="yesterday" +"%Y%m%d")
DATE="${DATE:-${LOGDATE}}"

for h5file in ${DATADIR}/${DATE}/*.h5; do
  mkdir -p ${CSVDIR}/${DATE}
  python3 ${BASE_DIR}/scripts/h5_to_csv.py $h5file ${WORKDIR}/${DATE}

# combine all into single csv
awk '(NR == 1) || (FNR > 1)' ${WORKDIR}/${DATE}}/*.csv > ${CSVDIR}/${DATE}.csv

# cleanup
rm -rf "${CSVDIR}/${DATE}"
