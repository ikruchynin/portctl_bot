from netmiko import ConnectHandler


class Switch:
    """
    Базовий клас мережевого пристрою.
    Відповідає лише за SSH-зʼєднання та виконання команд.
    """

    def __init__(self, name, host, username, password, device_type):
        self.name = name
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type

    def _connect(self):
        return ConnectHandler(
            device_type=self.device_type,
            host=self.host,
            username=self.username,
            password=self.password,
        )

    def run_command(self, command):
        """
        Виконує одну show/exec-команду.
        """
        with self._connect() as conn:
            return conn.send_command(command)

    def run_config(self, commands):
        """
        Виконує набір конфігураційних команд.
        (Для пристроїв з config-mode)
        """
        with self._connect() as conn:
            return conn.send_config_set(commands)


    # -------- ПУБЛІЧНИЙ ІНТЕРФЕЙС --------

    def status(self, interface):
        raise NotImplementedError

    def show_interface_config(self, interface):
        raise NotImplementedError

    def show_running_config(self):
        raise NotImplementedError

    def get_logs(self, lines=10):
        raise NotImplementedError

    def up(self, interface):
        raise NotImplementedError

    def down(self, interface):
        raise NotImplementedError

    def set_access_vlan(self, interface, vlan):
        raise NotImplementedError

    def add_trunk_vlan(self, interface, vlan):
        raise NotImplementedError



# =========================================================


class CiscoSwitch(Switch):
    """
    Реалізація для Cisco IOS
    """

    # -------- READ-ONLY --------

    def status(self, interface):
        return self.run_command(f"show interface {interface}")

    def show_interface_config(self, interface):
        return self.run_command(
            f"show running-config interface {interface}"
        )

    def show_running_config(self):
        return self.run_command("show running-config | begin vlan") #begin vlan для скорочення виводу

    def get_logs(self, lines=10):
        output = self.run_command("show logging")
        log_lines = output.splitlines()[-lines:]
        return "\n".join(log_lines)

    # -------- PORT CONTROL --------

    def up(self, interface):
        return self.run_config([
            f"interface {interface}",
            "no shutdown",
        ])

    def down(self, interface):
        return self.run_config([
            f"interface {interface}",
            "shutdown",
        ])

    # -------- VLAN --------

    def set_access_vlan(self, interface, vlan):
        return self.run_config([
            f"interface {interface}",
            f"switchport access vlan {vlan}",
        ])

    def add_trunk_vlan(self, interface, vlan):
        return self.run_config([
            f"interface {interface}",
            f"switchport trunk allowed vlan add {vlan}",
        ])