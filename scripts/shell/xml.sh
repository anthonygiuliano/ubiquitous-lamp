#!bin/zsh

# selects the value of the assignedTo property of each ruleEntry element
xml sel -t -v /_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo force-app/main/default/assignmentRules/Case.assignmentRules-meta.xml

# changes the value of the assignedTo property of each ruleEntry element
# -L for in place edit
# -P for preserve format
# -N for namespace
xml ed -L -P -u /_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo -v agiuliano@gmail.com force-app/main/default/assignmentRules/Case.assignmentRules-meta.xml