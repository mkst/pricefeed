#!/bin/bash

BASE_DIR="$( readlink -f "$( dirname "$0" )/../" )"

# default paths
HDBDIR="${HDBDIR:-${BASE_DIR}/hdb}"
SCRIPTDIR="${SCRIPTDIR:-${BASE_DIR}/scripts}"
QBIN="${QBIN:-${HOME}/q/l64/q}"

# process yesterday by default
LOGDATE=$(date --date="yesterday" +"%Y.%m.%d")
DATE="${DATE:-${LOGDATE}}"

# 4 worker threads by default
SLAVES=4

TABLES=$(ls -1a hdb/*/${DATE}/ | grep book | sort | uniq)

for table in ${TABLES}; do
    echo "Processing ${table}..."
    ${QBIN} ${SCRIPTDIR}/aggregate.q -hdbDir ${HDBDIR} -date ${DATE} -table ${table} -providers ${BASE_DIR}/config/providers.csv -s ${SLAVES} </dev/null
done
