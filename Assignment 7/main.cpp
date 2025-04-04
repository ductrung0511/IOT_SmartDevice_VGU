#include <Arduino.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);  // Set the LCD address (0x27) for a 16 chars and 2-line display

#define M_PIN A1  // Define the moisture sensor pin

unsigned long previousMillis = 0;  // Variable to store last time the display was updated
int secondCount = 0;  // Variable to count seconds

void setup() {
    Serial.begin(9600);  // Start the Serial communication
    pinMode(M_PIN, INPUT);  // Set the moisture pin as input to read analog data
    lcd.begin();  // Initialize the LCD
    lcd.backlight();  // Turn on the LCD backlight
    lcd.setCursor(0, 0);  // Set the cursor to the first position
    lcd.print("Time: 0s");  // Display initial time
}

void loop() {
    unsigned long currentMillis = millis();  // Get the current time in milliseconds

    // Check if 1 second has passed
    if (currentMillis - previousMillis >= 1000) {
        // Save the last time the display was updated
        previousMillis = currentMillis;

        // Increment the second count
        secondCount++;

        // Update the display with the new time
        lcd.clear();  // Clear the previous time
        lcd.setCursor(0, 0);  // Set cursor to the first line
        lcd.print("Time: " + String(secondCount) + "s");  // Display the time in seconds
    }

    // Read moisture value
    int moisture = analogRead(M_PIN);

    // Print moisture value to Serial Monitor
    String displayText = "MOISTURE: " + String(moisture);
    Serial.println(displayText);

    // Display the moisture value on LCD (below the time counter)
    lcd.setCursor(0, 1);  // Set cursor to the second line
    lcd.print(displayText);

    delay(1000);  // Wait briefly before the next loop iteration
}
