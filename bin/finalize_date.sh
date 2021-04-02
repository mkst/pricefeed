#!/bin/bash

BASE_DIR="$( cd "$( dirname "$0" )/../" &> /dev/null && pwd )"

# default paths
DATADIR="${DATADIR:-${BASE_DIR}/data}"
SCRIPTDIR="${SCRIPTDIR:-${BASE_DIR}/scripts}"

# process yesterday by default
LOGDATE=$(date --date="yesterday" +"%Y-%m-%d")
DATE="${DATE:-${LOGDATE}}"

for h5file in ${DATADIR}/${DATE}/*.h5; do
  if [ ! -e $h5file ]; then
    echo "No files to process."
    exit 0
  fi
  python3 ${SCRIPTDIR}/finalize_h5.py "${h5file}" "${h5file}.tmp"
  if [ "$?" -ne "0" ]; then
    echo "finalize_h5 did not return 0 status while finalising ${h5file}, exiting."
    rm -f "${h5file}.tmp"
    exit 1
  fi
  # overwrite
  mv "${h5file}.tmp" "${h5file}"
  if [ "$?" -ne "0" ]; then
    echo "error occurred during mv operation, exiting."
    exit 2
  fi
done
