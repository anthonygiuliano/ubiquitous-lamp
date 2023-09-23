#!bin/zsh

jq '.replacements[0].stringToReplace="blah"' sfdx-project.json > .tmp.json
mv .tmp.json sfdx-project.json