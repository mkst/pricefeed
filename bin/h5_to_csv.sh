#!/bin/bash

BASE_DIR="$( cd "$( dirname "$0" )/../" &> /dev/null && pwd )"

# default paths
DATADIR="${DATADIR:-${BASE_DIR}/data}"
CSVDIR="${CSVDIR:-${BASE_DIR}/data/csv}"
WORKDIR="${WORKDIR:-${BASE_DIR}/work}"
SCRIPTDIR="${SCRIPTDIR:-${BASE_DIR}/scripts}"


# process yesterday by default
LOGDATE=$(date --date="yesterday" +"%Y-%m-%d")
DATE="${DATE:-${LOGDATE}}"

for h5file in ${DATADIR}/${DATE}/*.h5; do
  if [ ! -e $h5file ]; then
    echo "No files to process."
    exit 0
  fi
  mkdir -p ${CSVDIR}/${DATE}
  python3 ${SCRIPTDIR}/h5_to_csv.py $h5file ${CSVDIR}/${DATE} book
  python3 ${SCRIPTDIR}/h5_to_csv.py $h5file ${CSVDIR}/${DATE} bbo
done

# combine all into single csv
awk '(NR == 1) || (FNR > 1)' ${CSVDIR}/${DATE}/bbo*.csv > ${CSVDIR}/${DATE}.csv

# cleanup bbo
rm -rf ${CSVDIR}/${DATE}/bbo*.csv
