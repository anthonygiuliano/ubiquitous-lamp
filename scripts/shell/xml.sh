#!bin/zsh

xml sel -t -v /_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo tst.xml
xml ed -L -P -u /_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo -v agiuliano@gmail.com tst.xml
# -L for in place edit
# -P for preserve format
# -N for namespace