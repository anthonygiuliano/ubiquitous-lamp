#! bin/zsh
# https://help.sfdmu.com/key-features

SCRIPT_DIR="$(cd "$(dirname "$0")" || exit ; pwd -P)"
SFDMU_DIR=$SCRIPT_DIR/sfdmu
mkdir -p $SFDMU_DIR
sf sfdmu run --path ${SFDMU_DIR} --simulation --sourceusername ag.dev --targetusername ag.integration --usesf