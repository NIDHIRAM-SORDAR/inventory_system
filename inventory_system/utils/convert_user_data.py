# inventory_system/convert_user_data.py
import pandas as pd
import json

# Read the .xlsx file
df = pd.read_excel("./assets/credentials.xlsx")  # Replace with your .xlsx file path

# Convert to a list of dictionaries
user_data = df.to_dict(orient="records")

# Save to JSON
with open("user_data.json", "w") as f:
    json.dump(user_data, f, indent=4)

print("User data converted to user_data.json")