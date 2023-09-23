#!bin/zsh

# changes the value of the stringToReplace property of the first "replacements" element and writes the result to a temporary file
# and moves the temporary file back into its original location
jq '.replacements[0].stringToReplace="blah"' sfdx-project.json > .tmp.json
mv .tmp.json sfdx-project.json

# iterates over the array of records and prints the Username field
jq -r '.result.records[].Username' scripts/soql/user.json