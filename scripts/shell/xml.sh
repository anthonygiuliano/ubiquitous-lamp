#!bin/zsh

USER_NODES=(/_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo /_:EscalationRules/_:escalationRule/_:ruleEntry/_:escalationAction/_:assignedTo /_:EscalationRules/_:escalationRule/_:ruleEntry/_:escalationAction/_:notifyTo)

find force-app/main/default/assignmentRules/ -type f -print0 | while IFS= read -r -d $'\0' file; do
	xml sel -t -v /_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo $file | while IFS= read -r -d ' ' word; do
	done
done

# selects the value of the assignedTo property of each ruleEntry element
xml sel -t -v /_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo force-app/main/default/assignmentRules/Case.assignmentRules-meta.xml

# changes the value of the assignedTo property of each ruleEntry element
# -L for in place edit
# -P for preserve format
# -N for namespace
# xml ed -L -P -u /_:AssignmentRules/_:assignmentRule/_:ruleEntry/_:assignedTo -v agiuliano@gmail.com force-app/main/default/assignmentRules/Case.assignmentRules-meta.xml