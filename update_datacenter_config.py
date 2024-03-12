import json
from datetime import datetime

def add_entry_to_data():
    # Load existing data
    try:
        with open('datacenter.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("File not found. Starting with an empty list.")
        data = []

    # Prompt user for data
    rack_id = input("Enter Rack ID: ").upper()
    esxi_ip = input("Enter ESXI IP: ").upper()
    rack_unit_input = input("Enter Rack Unit (comma-separated for multiple, e.g., U1,U2): ")
    rack_unit = [unit.replace(" ", "").upper() for unit in rack_unit_input.split(',')]
    ilo_address = input("Enter ILO Address: ").upper()

    # Find or create the rack
    rack = next((item for item in data if item["Rack ID"] == rack_id), None)
    if not rack:
        rack = {"Rack ID": rack_id, "ESXIs": {}}
        data.append(rack)

    # Add the ESXI entry
    rack['ESXIs'][esxi_ip] = {
        "Rack Unit": rack_unit,
        "ILO": ilo_address
    }

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"datacenter_{timestamp}.json"

    # Write data to new file
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    
    print(f"Data saved to {filename}")

add_entry_to_data()
