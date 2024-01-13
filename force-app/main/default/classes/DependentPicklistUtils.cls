/*
 * Apex doesn't expose dependent picklist info directly, but it's possible to expose.
 * Approach:
 *  * Schema.PicklistEntry doesn't expose validFor tokens, but they are there, and can be accessed by serializing to JSON
 *    (and then for convenience, deserializing back into an Apex POJO)
 *  * validFor tokens are converted from base64 representations (e.g. gAAA) to binary (100000000000000000000)
 *    each character corresponds to 6 bits, determined by normal base64 encoding rules.
 *  * The binary bits correspond to controlling values that are active - e.g. in the example above, this dependent option
 *    is available for the first controlling field only.
 *
 * by Benj Kamm, 2017
 * extended by Anthony Giuliano, 2024
 * CC BY-SA 3.0 (http://creativecommons.org/licenses/by-sa/3.0/us/)
 */

public with sharing class DependentPicklistUtils {
  public static Map<String, List<String>> getDependentValues(
    String objectName,
    String dependentName
  ) {
    Map<String, SObjectField> fieldMap = getDependentAndController(
      objectName,
      dependentName
    );
    SObjectField dependent = fieldMap.get('dependent');
    SObjectField controller = fieldMap.get('controller');

    // validFor property cannot be accessed via a method or a property,
    // so we need to serialize the PicklistEntry object and then deserialize into a wrapper.
    List<PicklistEntry> controllerEntries = controller.getDescribe()
      .getPicklistValues();
    List<PicklistEntry> fieldEntries = dependent.getDescribe()
      .getPicklistValues();
    List<PicklistEntryWrapper> fieldEntryWrappers = DependentPicklistUtils.wrapEntries(
      fieldEntries
    );

    // Set up the return container - Map<ControllerValue, List<DependentValues>>
    Map<String, List<String>> resultMap = new Map<String, List<String>>();
    List<String> controllingValues = new List<String>();

    for (Schema.PicklistEntry ple : controllerEntries) {
      String label = ple.getLabel();
      resultMap.put(label, new List<String>());
      controllingValues.add(label);
    }

    for (PicklistEntryWrapper plew : fieldEntryWrappers) {
      String label = plew.label;
      String validForBits = base64ToBits(plew.validFor);
      for (Integer i = 0; i < validForBits.length(); i++) {
        // For each bit, in order: if it's a 1, add this label to the dependent list for the corresponding controlling value
        String bit = validForBits.mid(i, 1);
        if (bit == '1') {
          resultMap.get(controllingValues.get(i)).add(label);
        }
      }
    }

    return resultMap;
  }

  public static List<String> getDependentValues(
    String objectName,
    String dependentName,
    String controllerValue
  ) {
    Map<String, List<String>> resultMap = getDependentValues(
      objectName,
      dependentName
    );
    return resultMap?.get(controllerValue);
  }

  public static String getControllerName(
    String objectName,
    String dependentName
  ) {
    Map<String, SObjectField> fieldMap = getDependentAndController(
      objectName,
      dependentName
    );
    SObjectField controller = fieldMap.get('controller');
    return controller.getDescribe().getName();
  }

  public static List<String> getControllerValues(
    String objectName,
    String dependentName
  ) {
    Map<String, SObjectField> fieldMap = getDependentAndController(
      objectName,
      dependentName
    );
    SObjectField dependent = fieldMap.get('dependent');
    SObjectField controller = fieldMap.get('controller');

    List<PicklistEntry> controllerEntries = controller.getDescribe()
      .getPicklistValues();
    List<String> controllerValues = new List<String>();
    for (Schema.PicklistEntry ple : controllerEntries) {
      String label = ple.getLabel();
      controllerValues.add(label);
    }
    return controllerValues;
  }

  public static Map<String, SObjectField> getDependentAndController(
    String objectName,
    String dependentName
  ) {
    List<String> objectNameList = new List<String>{ objectName };
    DescribeSObjectResult objectDescribe;
    SObjectField dependent;
    SObjectField controller;
    Map<String, SObjectField> resultMap = new Map<String, SObjectField>();
    try {
      objectDescribe = Schema.describeSObjects(objectNameList)[0];
      dependent = objectDescribe.getMap().get(dependentName);
      controller = dependent.getDescribe().getController();
    } catch (InvalidParameterValueException e) {
      System.debug(e.getMessage());
    }
    resultMap.put('dependent', dependent);
    resultMap.put('controller', controller);
    return resultMap;
  }

  // Convert decimal to binary representation (alas, Apex has no native method :-(
  // e.g. 4 => '100', 19 => '10011', etc.
  // Method: Divide by 2 repeatedly until 0. At each step note the remainder (0 or 1).
  // These, in reverse order, are the binary.
  public static String decimalToBinary(Integer val) {
    String bits = '';
    while (val > 0) {
      Integer remainder = Math.mod(val, 2);
      val = Integer.valueOf(Math.floor(val / 2));
      bits = String.valueOf(remainder) + bits;
    }
    return bits;
  }

  // Convert a base64 token into a binary/bits representation
  // e.g. 'gAAA' => '100000000000000000000'
  public static String base64ToBits(String validFor) {
    if (String.isEmpty(validFor))
      return '';

    String validForBits = '';

    for (Integer i = 0; i < validFor.length(); i++) {
      String thisChar = validFor.mid(i, 1);
      Integer val = base64Chars.indexOf(thisChar);
      String bits = decimalToBinary(val).leftPad(6, '0');
      validForBits += bits;
    }

    return validForBits;
  }

  private static final String base64Chars =
    '' +
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
    'abcdefghijklmnopqrstuvwxyz' +
    '0123456789+/';

  private static List<PicklistEntryWrapper> wrapEntries(
    List<Schema.PicklistEntry> entries
  ) {
    return (List<PicklistEntryWrapper>) JSON.deserialize(
      JSON.serialize(entries),
      List<PicklistEntryWrapper>.class
    );
  }

  public class PicklistEntryWrapper {
    public String active { get; set; }
    public String defaultValue { get; set; }
    public String label { get; set; }
    public String value { get; set; }
    public String validFor { get; set; }
  }
}
