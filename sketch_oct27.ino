
#include <LiquidCrystal.h>

// Initialize the LCD (pins connected to Arduino)
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);
String receivedCommand = ""; // Store the received command

void setup() {
  Serial.begin(9600); // Ensure baud rate matches the Python script
  lcd.begin(16, 2);   // Set up the LCD's number of columns and rows
  lcd.print("Ready..."); // Display initial message
}

void loop() {
  // Read input from the serial until newline character is detected
  while (Serial.available() > 0) {
    char receivedChar = Serial.read(); // Read the character from the serial buffer
    if (receivedChar == '\n') { // Check for end of command
      lcd.clear();             // Clear the LCD screen
      lcd.setCursor(0, 0);     // Set cursor to the beginning
      lcd.print("Command:");   // Display "Command:" on the first row
      lcd.setCursor(0, 1);     // Move to the second row
      lcd.print(receivedCommand); // Display the full command on the second line
      receivedCommand = "";    // Clear the command buffer for the next message
    } else {
      receivedCommand += receivedChar; // Accumulate characters into the command
    }
  }
}
