#!/bin/zsh

which sf > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo 'Please install and set up @salesforce/cli'
  exit 1
fi

AUTHORIZED=$(npx sf org display --json | jq '.status')
if [ $AUTHORIZED -ne 0 ]; then
  echo 'Please set your default org'
  exit 1
fi

USERNAME_DEV=$(npx sf org display --json | jq '.result.username' | tr -d '"')
ORG_ID_DEV=$(npx sf org display --json | jq '.result.id' | tr -d '"')

export $USERNAME_DEV
export $ORG_ID_DEV

# source scripts/shell/environments.sh
