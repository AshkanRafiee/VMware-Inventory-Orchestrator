import json
import ssl
import logging
import datetime
from pyVim import connect
from getpass import getpass
from pyVmomi import vim, vmodl

logging.basicConfig(level=logging.INFO)

def create_ssl_context(ignore_ssl):
    """Create and return an SSL context based on the ignore_ssl flag."""
    context = ssl.create_default_context()
    if ignore_ssl:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context

def connect_to_vmware(host, username, password, ignore_ssl=True):
    """Establish connection to VMware vCenter with the option to ignore SSL certificate verification."""
    context = create_ssl_context(ignore_ssl)
    try:
        return connect.SmartConnect(host=host, user=username, pwd=password, sslContext=context)
    except vmodl.MethodFault as error:
        logging.error(f"Failed to connect to VMware vCenter: {error}")
    except ssl.SSLError as ssl_error:
        logging.error(f"SSL error encountered: {ssl_error}")
    except Exception as generic_error:
        logging.error(f"An unexpected error occurred: {generic_error}")
    return None

def fetch_vm_inventory(content, fetch_custom_attributes):
    """Fetches VM inventory, including custom attributes if specified."""
    logging.info("Fetching VM inventory")
    start_time = datetime.datetime.now()
    properties = ["name", "config.hardware.numCPU", "config.hardware.memoryMB", "guest.net",
                  "guest.ipAddress", "config.hardware.device", "summary.customValue", "runtime.host"]
    virtual_machines = batch_fetch_properties(content, vim.VirtualMachine, properties)
    if fetch_custom_attributes:
        virtual_machines = process_custom_attributes(virtual_machines, content)
    fetch_time = datetime.datetime.now() - start_time
    logging.info(f"Fetched VM inventory in {fetch_time}")
    return virtual_machines

def batch_fetch_properties(content, obj_type, properties):
    """Batch fetch properties for a given VMware object type."""
    container_view = content.viewManager.CreateContainerView(container=content.rootFolder, type=[obj_type], recursive=True)
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=obj_type, pathSet=properties)
    
    traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(name="traverseEntities", path="view", skip=False, type=container_view.__class__)
    obj_spec = vmodl.query.PropertyCollector.ObjectSpec(obj=container_view, skip=True, selectSet=[traversal_spec])
    
    filter_spec = vmodl.query.PropertyCollector.FilterSpec(objectSet=[obj_spec], propSet=[property_spec])
    props = content.propertyCollector.RetrieveContents([filter_spec])
    container_view.Destroy()

    results = {obj.obj._moId: {prop.name: prop.val for prop in obj.propSet} for obj in props}
    return results

def process_custom_attributes(virtual_machines, content):
    """Processes custom attributes for each VM, replacing key IDs with their descriptive names."""
    all_custom_attributes = {f.key: f.name for f in content.customFieldsManager.field if f.managedObjectType in (vim.VirtualMachine, None)} if content.customFieldsManager and content.customFieldsManager.field else {}
    
    for vm_id, vm_properties in virtual_machines.items():
        custom_values = vm_properties.get("summary.customValue", [])
        processed_custom_values = {all_custom_attributes.get(cv.key, cv.key): cv.value for cv in custom_values}
        vm_properties["summary.customValue"] = processed_custom_values
    return virtual_machines

def process_vm_info(vm_properties):
    """Processes and returns a dictionary of key VM information."""
    harddisk_info = [
        {"label": device.deviceInfo.label, "capacity_gb": round(device.capacityInKB / (1024**2), 2), "datastore": device.backing.datastore.summary.name}
        for device in vm_properties.get("config.hardware.device", []) if isinstance(device, vim.vm.device.VirtualDisk)
    ]

    vm_info = {
        "host": vm_properties.get("runtime.host").name,
        "name": vm_properties["name"],
        "cpu_cores": vm_properties["config.hardware.numCPU"],
        "memory_gb": vm_properties["config.hardware.memoryMB"] / 1024,
        "harddisk_info": harddisk_info,
        "custom_attributes": vm_properties.get("summary.customValue", {}),
        "ip_info": extract_ips(vm_properties)
    }
    return vm_info

def extract_ips(vm_properties):
    """Extracts IP information from VM properties."""
    ip_info = {}
    for nic in vm_properties.get("guest.net", []):
        if nic.ipConfig:
            interface_name = nic.network
            ip_info[interface_name] = [f"{ip.ipAddress}/{ip.prefixLength}" for ip in nic.ipConfig.ipAddress]
    return ip_info

def append_vm_to_esxi(vm, esxis):
    """Appends VM information to the corresponding ESXi host in the given data structure."""
    for esxi in esxis:
        if vm['host'] in esxi['ESXIs']:
            esxi['ESXIs'][vm['host']].setdefault('VMs', []).append(vm)
            return True
    return False

def merge_vminfo_with_rack_data(vminfo, rack_data):
    """Merges VM information with manual rack data."""
    for vm in vminfo:
        if not append_vm_to_esxi(vm, rack_data):
            logging.info(f"No matching ESXi found for VM '{vm['name']}' on host '{vm['host']}'")
    return rack_data

def load_rack_data(path):
    """Loads rack data from a specified JSON file."""
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"File not found: {path}")
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from file: {path}")
    return {}

def main():
    """Main function to orchestrate the VM inventory process."""
    host = input("Enter vCenter hostname/IP: ")
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    connection = connect_to_vmware(host, username, password)

    if connection:
        content = connection.RetrieveContent()
        vm_inventory_data = fetch_vm_inventory(content, True)
        vminfo = [process_vm_info(vm_properties) for vm_properties in vm_inventory_data.values()]

        # rack_data_path = input("Enter path to datacenter.json: ")
        rack_data_path = 'datacenter.json'
        rack_data = load_rack_data(rack_data_path)
        final_data = merge_vminfo_with_rack_data(vminfo, rack_data)

        # Filter VMs with empty custom attributes
        vms_with_empty_custom_attributes = [vm for vm in vminfo if not vm["custom_attributes"]]

        # Save the final data to a JSON file
        with open('final_data.json', 'w') as f:
            json.dump(final_data, f, indent=4)
        
        # Save VMs with empty custom attributes to a JSON file
        with open('vms_with_empty_custom_attributes.json', 'w') as f:
            json.dump(vms_with_empty_custom_attributes, f, indent=4)

        logging.info("VMware inventory processing completed.")
    else:
        logging.error("Unable to connect to VMware vCenter.")

if __name__ == "__main__":
    main()
