#!/bin/bash

BASE_DIR="$( cd "$( dirname "$0" )/../" &> /dev/null && pwd )"

# default paths
ZIPDIR="${ZIPDIR:-${BASE_DIR}/zips}"
WORKDIR="${WORKDIR:-${BASE_DIR}/work}"
DATADIR="${DATADIR:-${BASE_DIR}/data}"
# process yesterday by default
LOGDATE=$(date --date="yesterday" +"%Y%m%d")
DATE="${DATE:-${LOGDATE}}"

FILES=$(python3 ${BASE_DIR}/scripts/zips_for_date.py ${DATE} --file-suffix _quote)

# process hour by hour
for file in ${FILES}; do
  ZIPFILE="${ZIPDIR}/${file}.zip"
  LOGFILE="${WORKDIR}/${file}.log"
  # unzip
  echo "unzip ${ZIPFILE}"
  unzip "${ZIPFILE}" -d ${WORKDIR}/
  if [ "$?" -ne "0" ]; then
    echo "unzip did not return 0 status while unzipping ${ZIPFILE}, exiting."
    exit
  fi
  # process
  echo "process ${LOGFILE}"
  python3 offline.py --workdir "${WORKDIR}" --outdir "${DATADIR}" --infiles "${LOGFILE}"
  if [ "$?" -ne "0" ]; then
    echo "offline.py did not return 0 status while processing ${LOGFILE}, exiting."
    exit
  fi
  # last processed?
  echo -n "${file}" > ${WORKDIR}/last_processed
  # cleanup
  echo "cleanup ${LOGFILE}"
  rm -f "${LOGFILE}"
done

# 3. cleanup logs
rm -f ${WORKDIR}/${DATE}*.log 2>/dev/null
