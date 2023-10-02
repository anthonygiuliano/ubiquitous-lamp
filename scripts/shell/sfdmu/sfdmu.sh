#! bin/zsh
# https://help.sfdmu.com/key-features

SCRIPT_DIR="$(cd "$(dirname "$0")" || exit ; pwd -P)"
sf sfdmu run --path ${SCRIPT_DIR} --simulation --sourceusername ag.dev --targetusername ag.integration --usesf