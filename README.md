portctl_bot

Telegram bot for emergency port control on network switches. For educational purposes

The bot is designed as a reserve management tool for emergency situations
when standard management interfaces (Web / GUI / VPN / NMS) are unavailable or inconvenient.
It is not a replacement for CLI or full-scale network management systems.

The bot performs only point actions on explicitly defined ports and does not modify
configuration outside of user commands.

## Usage

Run the bot using Docker Compose:

```bash
docker compose up -d
```

## Environment variables

Create `.env` file:

```env
BOT_TOKEN=PASTE_TELEGRAM_BOT_TOKEN_HERE
ALLOWED_USERS=123456789,987654321
```

## Configuration file

Create `config.yml` and mount it into the container as a read-only volume.
This file is the single source of truth and is not modified at runtime.

```yaml
switches:
  sw1:
    type: cisco_ios
    host: 10.0.0.1
    user: admin
    password: PASSWORD_HERE
    interfaces:
      client1: Ethernet0/1
      uplink1: GigabitEthernet0/48
    protected:
      - uplink1
```

## Docker Compose example

```yaml
services:
  portctl_bot:
    image: ikruchinin/portctl_bot:latest
    restart: always
    env_file: .env
    volumes:
      - ./config.yml:/app/config.yml:ro
```

## Notes

The bot operates only on ports defined in `config.yml`.
If a port alias is not present in the configuration, the command is not executed.
Protected ports require explicit confirmation using `force` or `!`.
VLAN numbers are not validated by the bot and are passed directly to the device.
CLI errors are returned as-is from the network equipment.
The bot is intended for low-frequency emergency use only.
