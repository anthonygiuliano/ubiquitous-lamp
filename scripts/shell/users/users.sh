#!/bin/zsh

DEV_ALIAS=dev
INTEGRATION_ALIAS=integration
UAT_ALIAS=uat
PRE_PROD_ALIAS=preprod
PROD_ALIAS=prod
ENVS=($DEV_ALIAS $INTEGRATION_ALIAS $UAT_ALIAS $PRE_PROD_ALIAS $PROD_ALIAS)

DEV_HOST=resilient-hawk-2xyvby.com
INTEGRATION_HOST=resilient-hawk-2xyvby.com
UAT_HOST=resilient-raccoon-2evij2.com
PRE_PROD_HOST=creative-panda-kbkazv.com
PROD_HOST=resourceful-wolf-ma8qhs.com
HOSTS=($DEV_HOST $INTEGRATION_HOST $UAT_HOST $PRE_PROD_HOST $PROD_HOST)

SCRIPT_DIR="$(cd "$(dirname "$0")" || exit ; pwd -P)"
OUTPUT_DIR=$SCRIPT_DIR/data

mkdir -p $OUTPUT_DIR

# Iterate over the array
for i in "${ENVS[@]}"
do
	sf data query --file $SCRIPT_DIR/../../soql/user.soql --result-format csv --target-org ag.$i | awk 'BEGIN{FS=OFS=","} NR==1{print $0,"UsernameSplit"} NR>1{split($2,a,"@"); print $0,a[1]}' > $OUTPUT_DIR/$i.csv
done
