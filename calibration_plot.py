import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Sample data: Voltage (sensor readings) and Gravimetric Soil Moisture (%)
voltage_values = [2883, 2331, 1527]  # Example voltage values
moisture_values = [83.3, 62.5, 37.5]  # Example moisture percentages

# 22 - 12 = 10 / 12 = 0.833  | 13 - 8 = 5 / 8 = 62,5 %  | 11 - 8 = 3 / 8 = 37,5 % 

# Perform linear regression to find the best-fit line
slope, intercept, r_value, p_value, std_err = linregress(voltage_values, moisture_values)
print(f"Equation: y = {slope:.4f}x + {intercept:.4f}")
# Generate x values for the line
x_values = np.linspace(min(voltage_values), max(voltage_values), 100)
y_values = slope * x_values + intercept

# Plot the data points
plt.scatter(voltage_values, moisture_values, color='red', label='Data Points')
plt.plot(x_values, y_values, linestyle='--', color='blue', label='Best Fit Line')

# Labels and title
plt.xlabel('Sensor Voltage (0-1023)')
plt.ylabel('Gravimetric Soil Moisture (%)')
plt.title('Soil Moisture vs. Sensor Voltage')
plt.legend()
plt.grid()

# Show the plot
plt.show()