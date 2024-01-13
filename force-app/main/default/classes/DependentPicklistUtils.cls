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
    // Get the dependent and controlling fields from the dependent field name
    Map<String, SObjectField> fieldMap = getDependentAndController(
      objectName,
      dependentName
    );
    SObjectField dependent = fieldMap.get('dependent');
    SObjectField controller = fieldMap.get('controller');

    // Get the picklist values for the dependent and controlling fields
    List<PicklistEntry> controllerEntries = controller.getDescribe()
      .getPicklistValues();
    List<PicklistEntry> fieldEntries = dependent.getDescribe()
      .getPicklistValues();

    // Wrap the dependent field's picklist entries into PicklistEntryWrapper objects
    // This is done to access the validFor property, which is not directly accessible
    List<PicklistEntryWrapper> fieldEntryWrappers = DependentPicklistUtils.wrapEntries(
      fieldEntries
    );

    // Initialize the map to store the final result
    // The map's keys are the controlling field values, and the values are lists of dependent field values
    Map<String, List<String>> resultMap = new Map<String, List<String>>();
    List<String> controllingValues = new List<String>();

    // Populate the resultMap with the controlling field values and initialize the dependent field lists
    for (Schema.PicklistEntry ple : controllerEntries) {
      String label = ple.getLabel();
      resultMap.put(label, new List<String>());
      controllingValues.add(label);
    }

    // For each dependent field value, determine which controlling field values it's valid for
    // This is done by converting the validFor property to bits and checking each bit
    // If a bit is 1, the dependent field value is valid for the corresponding controlling field value
    for (PicklistEntryWrapper plew : fieldEntryWrappers) {
      String label = plew.label;
      String validForBits = base64ToBits(plew.validFor);
      for (Integer i = 0; i < validForBits.length(); i++) {
        String bit = validForBits.mid(i, 1);
        if (bit == '1') {
          resultMap.get(controllingValues.get(i)).add(label);
        }
      }
    }

    // Return the map of controlling field values to dependent field values
    return resultMap;
  }

  public static List<String> getDependentValues(
    String objectName,
    String dependentName,
    String controllerValue
  ) {
    // Call the getDependentValues method to get a map of dependent picklist values
    // for the given object and field. The map's keys are the controlling field values,
    // and the values are lists of dependent field values.
    Map<String, List<String>> resultMap = getDependentValues(
      objectName,
      dependentName
    );

    // Return the list of dependent picklist values for the given controlling field value.
    // If the controlling field value is not in the map, this will return null.
    return resultMap?.get(controllerValue);
  }

  public static String getControllerName(
    String objectName,
    String dependentName
  ) {
    // Call the getDependentAndController method to get a map of the dependent and controlling fields
    // for the given object and field.
    Map<String, SObjectField> fieldMap = getDependentAndController(
      objectName,
      dependentName
    );

    // Retrieve the controlling field from the map.
    SObjectField controller = fieldMap.get('controller');

    // Return the API name of the controlling field.
    return controller.getDescribe().getName();
  }

  public static List<String> getControllerValues(
    String objectName,
    String dependentName
  ) {
    // Call the getDependentAndController method to get a map of the dependent and controlling fields
    // for the given object and field.
    Map<String, SObjectField> fieldMap = getDependentAndController(
      objectName,
      dependentName
    );

    // Retrieve the dependent and controlling fields from the map.
    SObjectField dependent = fieldMap.get('dependent');
    SObjectField controller = fieldMap.get('controller');

    // Get the picklist values for the controlling field.
    List<PicklistEntry> controllerEntries = controller.getDescribe()
      .getPicklistValues();

    // Initialize a list to store the labels of the controlling field's picklist values.
    List<String> controllerValues = new List<String>();

    // Iterate over the controlling field's picklist entries, adding each label to the list.
    for (Schema.PicklistEntry ple : controllerEntries) {
      String label = ple.getLabel();
      controllerValues.add(label);
    }

    // Return the list of labels.
    return controllerValues;
  }

  public static Map<String, SObjectField> getDependentAndController(
    String objectName,
    String dependentName
  ) {
    // Create a list with the object name
    List<String> objectNameList = new List<String>{ objectName };

    // Declare variables to hold the object description, dependent field, and controller field
    DescribeSObjectResult objectDescribe;
    SObjectField dependent;
    SObjectField controller;

    // Initialize a map to hold the dependent and controller fields
    Map<String, SObjectField> fieldMap = new Map<String, SObjectField>();

    try {
      // Get the object description
      objectDescribe = Schema.describeSObjects(objectNameList)[0];

      // Get the dependent field from the object description
      dependent = objectDescribe.fields.getMap().get(dependentName);

      // Get the controller field from the dependent field description
      controller = dependent.getDescribe().getController();
    } catch (InvalidParameterValueException e) {
      // Log any exceptions that occur
      System.debug(e.getMessage());
    }

    // Add the dependent and controller fields to the map
    fieldMap.put('dependent', dependent);
    fieldMap.put('controller', controller);

    // Return the map
    return fieldMap;
  }

  // Convert decimal to binary representation (alas, Apex has no native method :-(
  // e.g. 4 => '100', 19 => '10011', etc.
  // Method: Divide by 2 repeatedly until 0. At each step note the remainder (0 or 1).
  // These, in reverse order, are the binary.
  public static String decimalToBinary(Integer val) {
    // Initialize an empty string to store the binary representation
    String bits = '';

    // While the input value is greater than 0
    while (val > 0) {
      // Calculate the remainder of the value divided by 2
      // This is the current bit in the binary representation
      Integer remainder = Math.mod(val, 2);

      // Divide the value by 2 and round down to the nearest integer
      // This effectively shifts the binary representation one place to the right
      val = Integer.valueOf(Math.floor(val / 2));

      // Add the current bit to the start of the binary representation
      bits = String.valueOf(remainder) + bits;
    }

    // Return the binary representation
    return bits;
  }

  // Convert a base64 token into a binary/bits representation
  // e.g. 'gAAA' => '100000000000000000000'
  public static String base64ToBits(String validFor) {
    // If the input string is empty, return an empty string
    if (String.isEmpty(validFor)) {
      return '';
    }

    // Initialize an empty string to store the binary representation
    String validForBits = '';

    // Iterate over each character in the input string
    for (Integer i = 0; i < validFor.length(); i++) {
      // Get the current character
      String thisChar = validFor.mid(i, 1);

      // Find the index of the current character in the base64Chars string
      // This is the decimal value of the character in base64 encoding
      Integer val = BASE64_CHARS.indexOf(thisChar);

      // Convert the decimal value to binary and pad it with zeros to the left to make it 6 bits long
      String bits = decimalToBinary(val).leftPad(6, '0');

      // Add the binary representation of the current character to the result string
      validForBits += bits;
    }

    // Return the binary representation of the input string
    return validForBits;
  }

  private static final String BASE64_CHARS =
    '' +
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
    'abcdefghijklmnopqrstuvwxyz' +
    '0123456789+/';

  private static List<PicklistEntryWrapper> wrapEntries(
    List<Schema.PicklistEntry> entries
  ) {
    // This method is used to wrap the picklist entries into PicklistEntryWrapper objects.
    // This is done to access the validFor property, which is not directly accessible from the PicklistEntry objects.
    
    // First, the picklist entries are serialized into a JSON string.
    // Then, the JSON string is deserialized into a list of PicklistEntryWrapper objects.
    // The resulting list of PicklistEntryWrapper objects is then returned.
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
