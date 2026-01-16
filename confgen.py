#!/usr/bin/env python3
"""
Offline generator for config.yml (portctl_bot).

- Generates aliases: client1..N, uplink1..N
- uplink aliases are added to protected
- interface name = prefix + number
- prefix is taken as-is (may contain trailing space)
"""

import os
import yaml


DEVICE_TYPES = ["cisco_ios"]


def ask(prompt):
    return input(f"{prompt}: ").strip()


def ask_raw(prompt):
    return input(f"{prompt}: ")


def port_name(prefix, num):
    return f"{prefix}{num}" if prefix else str(num)


def choose_device_type():
    print("Device types:")
    for i, t in enumerate(DEVICE_TYPES, 1):
        print(f"  {i}. {t}")
    n = int(ask("Choose device type (number)"))
    return DEVICE_TYPES[n - 1]


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def add_switch(config):
    name = ask("Switch name")
    device_type = choose_device_type()
    host = ask("Host/IP")
    user = ask("Username")
    password = ask("Password")

    print("Client ports (examples: 'GigabitEthernet0/', 'Ethernet ', empty = numeric)")
    client_prefix = ask_raw("Client port prefix")
    client_start = int(ask("Client port start number"))
    client_count = int(ask("Client port count"))

    print("Uplink ports (examples: 'GigabitEthernet0/', 'Ethernet ', empty = numeric)")
    uplink_prefix = ask_raw("Uplink port prefix")
    uplink_start = int(ask("Uplink port start number"))
    uplink_count = int(ask("Uplink port count"))

    sw = {
        "type": device_type,
        "host": host,
        "user": user,
        "password": password,
        "interfaces": {},
        "protected": [],
    }

    for i in range(client_count):
        num = client_start + i
        sw["interfaces"][f"client{i + 1}"] = port_name(client_prefix, num)

    for i in range(uplink_count):
        num = uplink_start + i
        alias = f"uplink{i + 1}"
        sw["interfaces"][alias] = port_name(uplink_prefix, num)
        sw["protected"].append(alias)

    if "switches" not in config:
        config["switches"] = {}

    config["switches"][name] = sw
    print(f"OK: added {name}")


def main():
    filename = ask("Output filename (Enter for config.yml)")
    if not filename:
        filename = "config.yml"
    if not (filename.endswith(".yml") or filename.endswith(".yaml")):
        filename += ".yml"

    config = {}

    if os.path.exists(filename):
        action = ask("Append to existing file? (y/n)").lower()
        if action == "y":
            config = load_config(filename)
        else:
            overwrite = ask("Overwrite file? (y/n)").lower()
            if overwrite != "y":
                print("Cancelled")
                return

    while True:
        add_switch(config)
        more = ask("Add one more switch? (y/n)").lower()
        if more != "y":
            break

    save_config(filename, config)
    print(f"OK: saved {filename}")


if __name__ == "__main__":
    main()

