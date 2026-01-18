import yaml

from switch import CiscoSwitch
# потенційно розширюється:
# from switch import DlinkSwitch, NosSwitch


CONFIG_PATH = "config.yml"


def create_device(name, sw):
    device_type = sw["type"]

    if device_type.startswith("cisco"):
        return CiscoSwitch(
            name=name,
            host=sw["host"],
            username=sw["user"],
            password=sw["password"],
            device_type=device_type,
        )

    else:
        raise ValueError(f"Unsupported device_type: {device_type}")


def load_switches(path=CONFIG_PATH):
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    # перевірка на порожній файл
    if data is None:
        raise ValueError("config.yml: empty file")

    raw_switches = data.get("switches")

    # перевірка на наявність або порожність switches
    if not raw_switches:
        raise ValueError("config.yml: 'switches' is empty or missing")

    switches = {}

    for name, sw in raw_switches.items():
        interfaces = sw.get("interfaces", {})
        protected = sw.get("protected", [])

        # перевірка на коректність даних в config.yml для запобігання непередбачуваної поведінки
        if not isinstance(interfaces, dict):
            raise TypeError(f"{name}: interfaces must be a dict")
        if not isinstance(protected, list):
            raise TypeError(f"{name}: protected must be a list")

        switches[name.lower()] = {
            "device": create_device(name, sw),
            "interfaces": interfaces,
            "protected": set(protected),
        }

    return switches
