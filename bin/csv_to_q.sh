#!/bin/bash

BASE_DIR="$( cd "$( dirname "$0" )/../" &> /dev/null && pwd )"

# default paths
CSVDIR="${CSVDIR:-${BASE_DIR}/data/csv}"
HDBDIR="${HDBDIR:-${BASE_DIR}/hdb}"
SCRIPTDIR="${SCRIPTDIR:-${BASE_DIR}/scripts}"
QBIN="${QBIN:-${HOME}/q/l64/q}"

LOGDATE=$(date --date="yesterday" +"%Y-%m-%d")
DATE="${DATE:-${LOGDATE}}"

for csv in ${CSVDIR}/${DATE}/book*.csv; do
  if [ ! -e $csv ]; then
    echo "No files to process."
    exit 0
  fi
  ${QBIN} ${SCRIPTDIR}/csv2q.q -infile $csv -outpath ${HDBDIR} -date ${DATE} -providers config/providers.csv < /dev/null
done
