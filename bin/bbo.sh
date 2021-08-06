#!/bin/bash

BASE_DIR="$( readlink -f "$( dirname "$0" )/../" )"

# default paths
HDBDIR="${HDBDIR:-${BASE_DIR}/hdb}"
SCRIPTDIR="${SCRIPTDIR:-${BASE_DIR}/scripts}"
CSVDIR="${CSVDIR:-${BASE_DIR}/csv}"
QBIN="${QBIN:-${HOME}/q/l32/q}"

# process yesterday by default
LOGDATE=$(date --date="yesterday" +"%Y.%m.%d")
DATE="${DATE:-${LOGDATE}}"

TABLES=$(ls -1a hdb/agg/${DATE}/ | grep pool | sort | uniq)

mkdir -p ${CSVDIR}/bbo/${DATE}/

for table in ${TABLES}; do
    echo "Processing ${table}..."
    ${QBIN} ${SCRIPTDIR}/bbo.q -hdbDir ${HDBDIR} -date ${DATE} -table ${table} -outDir ${CSVDIR}/bbo/${DATE}/ </dev/null
done

# combine all into single csv
awk '(NR == 1) || (FNR > 1)' ${CSVDIR}/bbo/${DATE}/*.csv > ${CSVDIR}/bbo/${DATE}.csv

# cleanup bbo
rm -rf ${CSVDIR}/bbo/${DATE}
