#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" &> /dev/null && pwd )"
ZIPDIR="${ZIPDIR:-${SCRIPT_DIR}/zips}"
WORKDIR="${WORKDIR:-${SCRIPT_DIR}/work}"
DATADIR="${DATADIR:-${SCRIPT_DIR}/data}"
LOGDATE=$(date --date="yesterday" +"%Y%m%d")
DATE="${DATE:-${LOGDATE}}"

# 1. unzip logs into workdir
echo "Extracting ${ZIPDIR}/${DATE}*.zip into ${WORKDIR}"
unzip -n "${ZIPDIR}/${DATE}*.zip" -d ${WORKDIR}/

if [ "$?" -ne "0" ]; then
  echo "unzip did not return 0 status, exiting."
  exit
fi

# 2. process logs
echo "Processing logs"
echo "python3 offline.py --infiles ${WORKDIR}/${DATE}*.log --workdir "${WORKDIR}" --outdir "${DATADIR}""

python3 offline.py --workdir "${WORKDIR}" --outdir "${DATADIR}" --infiles ${WORKDIR}/${DATE}*.log

# 3. cleanup logs
# rm - ${WORKDIR}/${DATE}*.log
