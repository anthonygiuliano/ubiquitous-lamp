List<String> objectName = new List<String>{ 'Account' };
String fieldName = 'UpsellOpportunity__c';
DescribeSObjectResult obj;
SObjectField field;

List<DescribeSObjectResult> results = new List<DescribeSObjectResult>();
Map<String, DescribeSObjectResult> resultsMap = new Map<String, DescribeSObjectResult>();
Map<String, List<SObjectField>> fieldMap = new Map<String, List<SObjectField>>();
try {
  obj = Schema.describeSObjects(objectName)[0];
  field = obj.fields.getMap().get(fieldName);
} catch (InvalidParameterValueException e) {
  System.debug(e.getMessage());
}

System.debug(obj?.getName());
System.debug(field?.getDescribe().getName());
System.debug(field?.getDescribe().getController());
