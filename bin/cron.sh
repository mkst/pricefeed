#!/bin/bash

BASE_DIR="$( readlink -f "$( dirname "$0" )/../" )"

# default paths
WORKDIR="${WORKDIR:-${BASE_DIR}/work}"
ZIPDIR="${ZIPDIR:-${BASE_DIR}/zips}"
DATADIR="${DATADIR:-${BASE_DIR}/data}"
CSVDIR="${CSVDIR:-${BASE_DIR}/csv}"
HDBDIR="${HDBDIR:-${BASE_DIR}/hdb}"

# process yesterday by default
DATE=$(date --date="yesterday" +"%Y%m%d")

# ensure directories exist
mkdir -p "${DATADIR}"
mkdir -p "${CSVDIR}"
mkdir -p "${HDBDIR}"
mkdir -p "${WORKDIR}"

# process logs
sh ${BASE_DIR}/bin/offline.sh

# finalize date
sh ${BASE_DIR}/bin/finalize_date.sh

# create csvs
sh ${BASE_DIR}/bin/h5_to_csv.sh
