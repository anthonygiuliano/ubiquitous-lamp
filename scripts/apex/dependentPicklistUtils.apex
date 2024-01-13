String objectName = 'Account';
String fieldName = 'UpsellOpportunity__c';
Map<String,List<String>> valueMap = DependentPicklistUtils.getDependentValuesMap(objectName, fieldName);

for (String key : valueMap.keySet()) {
    System.debug('Controller Picklist Value: ' + key);
    System.debug('Dependent Picklist Values: ' + valueMap.get(key));
    System.debug('------------------');
}

String controllerValue = 'Customer - Direct';

List<String> dependentValues = DependentPicklistUtils.getDependentValuesMap(objectName, fieldName, controllerValue);
for (String value : dependentValues) {
    System.debug('Controlling Field Value: ' + controllerValue);
    System.debug('Dependent Picklist Value: ' + value);
}

Map<String, SObjectField> fieldMap = DependentPicklistUtils.getDependentAndController(objectName, fieldName);
for (String key : fieldMap.keySet()) {
    System.debug(key + ': ' + fieldMap.get(key));
    System.debug('------------------');
}