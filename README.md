# VMware Inventory Orchestrator
A toolkit for automating VMware VM inventory collection and rack configuration management.

## Overview

This project includes a suite of tools designed to efficiently manage and report on VMware virtual machine (VM) inventories within a data center environment. It consists of a primary script for fetching VM inventory from VMware vCenter and a utility script for managing rack configurations within a `datacenter.json` file.

## Features

- **VMware Inventory Collection:** Automates the collection of VM inventories from VMware vCenter, including details like CPU cores, memory, hard disk information, custom attributes, and IP information.
- **Rack Configuration Management:** Facilitates the addition and update of rack configurations, including ESXi host mappings, through a simple CLI interface.

## Requirements

Ensure the following prerequisites are met to use this project:

- Python 3.6+
- pyVmomi 7.0+

To install required Python packages:

```bash
pip install -r requirements.txt
```

## Installation

Clone this repository to your local machine:

```bash
git clone https://github.com/AshkanRafiee/vmware-inventory-orchestrator.git
cd vmware-inventory-orchestrator
```

## Configuration

1. **VMware Inventory Script (`vmware_inventory_orchestrator.py`):** Ready to run out of the box. You'll be prompted for vCenter credentials upon execution.

2. **Datacenter Configuration Update Script (`update_datacenter_config.py`):** Works with `datacenter.json` to update rack and ESXi configurations. No initial setup required beyond the JSON file structure.

## Usage

### Creating/Updating Rack Data

Run the configuration update script to modify `datacenter.json`:

```bash
python update_datacenter_config.py
```

Follow the prompts to input the necessary data.

## `datacenter.json` Format

The configuration file should adhere to the following format:

```json
[
    {
        "Rack Name": "Rack1",
        "ESXIs": {
            "ESXi1": {
                "Rack Unit": ["U1", "U2"],
                "VMs": [
                    ...
                ]
            }
        }
    }
]
```

### Fetching VM Inventory

Execute the main script from your terminal:

```bash
python vmware_inventory_orchestrator.py
```

Enter the vCenter hostname/IP, username, and password when prompted.


## Contributing

We welcome contributions to improve this project. Please open an issue first to discuss potential changes or additions.
