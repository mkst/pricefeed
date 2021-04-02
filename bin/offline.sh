#!/bin/bash

BASE_DIR="$( cd "$( dirname "$0" )/../" &> /dev/null && pwd )"

# default paths
ZIPDIR="${ZIPDIR:-${BASE_DIR}/zips}"
WORKDIR="${WORKDIR:-${BASE_DIR}/work}"
DATADIR="${DATADIR:-${BASE_DIR}/data}"
SCRIPTDIR="${SCRIPTDIR:-${BASE_DIR}/scripts}"

# process yesterday by default
LOGDATE=$(date --date="yesterday" +"%Y%m%d")
DATE="${DATE:-${LOGDATE}}"

FILES=$(python3 ${SCRIPTDIR}/zips_for_date.py ${DATE} --file-suffix _quote)

if [ "${SAFEMODE}" -eq 1 ]; then
  SAFEMODE_ARG="--safe-mode"
fi

# process hour by hour
for file in ${FILES}; do
  ZIPFILE="${ZIPDIR}/${file}.zip"
  LOGFILE="${WORKDIR}/${file}.log"
  # sanity
  if [ ! -f "${ZIPFILE}" ]; then
    echo "${ZIPFILE} not found, exiting."
    exit
  fi
  # unzip
  echo "unzip ${ZIPFILE}"
  unzip -o "${ZIPFILE}" -d ${WORKDIR}/
  if [ "$?" -ne "0" ]; then
    echo "unzip did not return 0 status while unzipping ${ZIPFILE}, exiting."
    exit
  fi
  # process
  echo "process ${LOGFILE}"
  if [ -n "${PROVIDER+x}" ]; then
    python3 "${BASE_DIR}/offline.py" --workdir "${WORKDIR}" --outdir "${DATADIR}" --infiles "${LOGFILE}" --hardcoded-provider "${PROVIDER}" ${SAFEMODE_ARG}
  else
    python3 "${BASE_DIR}/offline.py" --workdir "${WORKDIR}" --outdir "${DATADIR}" --infiles "${LOGFILE}" ${SAFEMODE_ARG}
  fi
  if [ "$?" -ne "0" ]; then
    echo "offline.py did not return 0 status while processing ${LOGFILE}, exiting."
    exit
  fi
  # last processed?
  echo -n "${file}" > ${WORKDIR}/last_processed
  # backup book/mappings
  if [ -e "${WORKDIR}/mappings.json" ]; then
    cp "${WORKDIR}/mappings.json" "${WORKDIR}/${file}_mappings.json"
  fi
  if [ -e "${WORKDIR}/book.json" ]; then
    cp "${WORKDIR}/book.json" "${WORKDIR}/${file}_book.json"
  fi
  # cleanup
  echo "cleanup ${LOGFILE}"
  rm -f "${LOGFILE}"
done

# 3. cleanup if successful
rm -f ${WORKDIR}/${DATE}*.log 2>/dev/null
rm -f ${WORKDIR}/${DATE}*.json 2>/dev/null
