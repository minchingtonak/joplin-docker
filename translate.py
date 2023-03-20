import yaml
import sys
import os
import re
import json

# TODO assumes string contains single env var
def find_env_var(env_value):
    return re.match(r'.*(\$\{([a-zA-Z0-9_-]+)\}).*', str(env_value))

def convert_networks_to_hcl(networks):
    hcl = ""
    for network_name, network_config in map(lambda name: (name[0], {} if not name[1] else name[1]),networks.items()):
        hcl += f'resource "docker_network" "{network_name}" {{\n'
        hcl += f'  name = "{network_name}"\n'

        if "driver" in network_config:
            hcl += f'  driver = "{network_config["driver"]}"\n'

        if "internal" in network_config:
            hcl += f'  internal = {network_config["internal"]}\n'

        if "ipv6" in network_config:
            hcl += f'  ipv6 = {network_config["ipv6"]}\n'

        if "attachable" in network_config:
            hcl += f'  attachable = {network_config["attachable"]}\n'

        if "options" in network_config:
            hcl += '  options = {\n'
            for opt_key, opt_value in network_config["options"].items():
                hcl += f'    "{opt_key}" = "{opt_value}"\n'
            hcl += '  }\n'

        if "ipam" in network_config:
            ipam = network_config["ipam"]
            if "driver" in ipam:
                hcl += f'  ipam_driver = "{ipam["driver"]}"\n'

            if "config" in ipam:
                for config in ipam["config"]:
                    hcl += '  ipam_config {\n'
                    for key, value in config.items():
                        hcl += f'    {key} = "{value}"\n'
                    hcl += '  }\n'

        hcl += '}\n\n'
    return hcl

def convert_to_hcl(service_name, service_config):
    hcl = f'resource "docker_container" "{service_name}" {{\n'
    hcl += f'  name = "{service_name}"\n'
    hcl += f'  image = "{service_config["image"]}"\n'

    if "restart" in service_config:
        hcl += f'  restart = "{service_config["restart"]}"\n'

    if "ports" in service_config:
        for port in service_config["ports"]:
            parts = port.split(':')
            if len(parts) == 2:
                hcl += f'  ports {{\n    internal = {parts[1]}\n    external = {parts[0]}\n  }}\n'
            else:
                hcl += f'  ports {{\n    internal = {parts[2]}\n    external = {parts[1]}\n    ip = "{parts[0]}"\n  }}\n'

    if "volumes" in service_config:
        for volume in service_config["volumes"]:
            parts = volume.split(":")
            is_path = "/" in parts[0] or "." in parts[0]
            hcl += f'  volumes {{\n    {"host_path" if is_path else "volume_name"} = "{os.path.abspath(parts[0]) if is_path else parts[0]}"\n    container_path = "{os.path.abspath(parts[1])}"\n'
            if len(parts) == 3:
                hcl += f'    read_only = {"true" if parts[2] == "ro" else "false"}\n'
            hcl += "  }\n"

    if "environment" in service_config:
        hcl += "  env = [\n"
        for env_var, env_value in service_config["environment"].items():
            matches = find_env_var(env_value)
            if matches is not None:
                hcl += f'    "{env_var}={str(env_value).replace(matches.group(1), f"${{var.{matches.group(2)}}}")}",\n'
            else:
                hcl += f'    "{env_var}={env_value}",\n'
        hcl += "  ]\n"

    if "networks" in service_config:
        for network in service_config["networks"]:
            hcl += f'  networks_advanced {{\n    name = "{network}"\n  }}\n'

    hcl += '}\n\n'
    return hcl

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <input_docker_compose_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print(f"File {input_file} not found")
        sys.exit(1)

    with open(input_file, "r") as file:
        docker_compose = yaml.safe_load(file)

    services = docker_compose.get("services", {})
    networks = docker_compose.get("networks", {})

    hcl_output = ""

    dangling_env_vars = {}
    for service_name, service_config in services.items():
        if 'environment' in service_config:
             for env_value in service_config["environment"].values():
                matches = find_env_var(env_value)
                if matches:
                    if matches.group(2) not in dangling_env_vars:
                        hcl_output += f'variable "{matches.group(2)}" {{\n  type = string\n}}\n\n'
                    dangling_env_vars[matches.group(2)] = ""


    hcl_output += convert_networks_to_hcl(networks)

    for service_name, service_config in services.items():
        hcl_output += convert_to_hcl(service_name, service_config)

    output_file = f'{"-".join(services.keys())}.tf'
    with open(output_file, "w") as file:
        file.write(hcl_output)

    print(f"Successfully converted {input_file} to {output_file}")

    with open("terraform.tfvars.json", "w") as file:
        json.dump(dangling_env_vars, file, indent=4)

    print("Wrote terraform.tfvars.json")

if __name__ == "__main__":
    main()
