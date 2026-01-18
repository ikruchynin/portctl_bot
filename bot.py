import os
import asyncio
from functools import wraps
from datetime import datetime

# Для локального старту без докер з файлом .env
#from dotenv import load_dotenv
#load_dotenv()

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from config import load_switches

# ================= НАЛАШТУВАННЯ =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
ALLOWED_USERS = {
    int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x
}
if not ALLOWED_USERS:
    raise RuntimeError("ALLOWED_USERS is empty or not set")

MAX_OUTPUT_LEN = 3900

# ================= ЗАВАНТАЖЕННЯ КОНФІГУ =================

SWITCHES = load_switches()

# ================= ІНІЦІАЛІЗАЦІЯ =================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= AUTH =================

def is_allowed(user_id):
    return user_id in ALLOWED_USERS


def auth_required(handler):
    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        if not is_allowed(message.from_user.id):
            await message.answer("Доступ заборонено")
            return

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[AUDIT] {ts} user={message.from_user.id} cmd={message.text}")

        return await handler(message, *args, **kwargs)
    return wrapper



# ================= HELPERS =================

def has_force_flag(text):
    parts = text.lower().split()
    return "force" in parts or text.strip().endswith("!")


def get_switch(name):
    return SWITCHES.get(name.lower())


def trim_output(text):
    if len(text) <= MAX_OUTPUT_LEN:
        return text
    return text[:MAX_OUTPUT_LEN] + "\n\n...(вивід обрізано)"

def switches_list_text():
    names = ", ".join(SWITCHES.keys())
    return f"Доступні свичі: {names}\n\n"



# ================= ТЕКСТИ =================

HELP_TEXT = (
    "Резервне керування мережевим обладнанням\n\n"
    "Команди:\n"
    "/up <switch> <alias> [force]\n"
    "/down <switch> <alias> [force]\n"
    "/status <switch> <alias>\n"
    "/show <switch> <alias>\n"
    "/showru <switch>\n"
    "/log <switch>\n"
    "/access <switch> <alias> <vlan> [force]\n"
    "/trunk <switch> <alias> <vlan> [force]\n"
    "/ports <switch>\n\n"
    "! Для protected портів потрібен force або !"
)

# ================= КОМАНДИ =================

@dp.message(Command("start"))
@dp.message(Command("help"))
@auth_required
async def help_handler(message: types.Message):
    await message.answer(switches_list_text() + HELP_TEXT)



@dp.message(Command("ports"))
@auth_required
async def ports_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Використання: /ports <switch>")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    text = "Доступні порти:\n"
    for alias in sw["interfaces"]:
        mark = " (protected)" if alias in sw["protected"] else ""
        text += f"- {alias}{mark}\n"

    await message.answer(text)


@dp.message(Command("status"))
@auth_required
async def status_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Використання: /status <switch> <alias>")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    alias = parts[2]
    interface = sw["interfaces"].get(alias)
    if not interface:
        await message.answer("Невідомий порт")
        return

    try:
        output = sw["device"].status(interface)
        await message.answer(trim_output(output))
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


@dp.message(Command("show"))
@auth_required
async def show_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Використання: /show <switch> <alias>")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    alias = parts[2]
    interface = sw["interfaces"].get(alias)
    if not interface:
        await message.answer("Невідомий порт")
        return

    try:
        output = sw["device"].show_interface_config(interface)
        await message.answer(trim_output(output))
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


@dp.message(Command("showru"))
@auth_required
async def showru_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Використання: /showru <switch>")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    try:
        output = sw["device"].show_running_config()
        await message.answer(trim_output(output))
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


@dp.message(Command("log"))
@auth_required
async def log_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Використання: /log <switch>")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    try:
        output = sw["device"].get_logs(lines=10)
        await message.answer(trim_output(output))
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


@dp.message(Command("up"))
@auth_required
async def up_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Використання: /up <switch> <alias> [force]")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    alias = parts[2]
    interface = sw["interfaces"].get(alias)
    if not interface:
        await message.answer("Невідомий порт")
        return

    if alias in sw["protected"] and not has_force_flag(message.text):
        await message.answer("Порт protected. Потрібен force або !")
        return

    try:
        sw["device"].up(interface)
        await message.answer("Порт увімкнено")
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


@dp.message(Command("down"))
@auth_required
async def down_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Використання: /down <switch> <alias> [force]")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    alias = parts[2]
    interface = sw["interfaces"].get(alias)
    if not interface:
        await message.answer("Невідомий порт")
        return

    if alias in sw["protected"] and not has_force_flag(message.text):
        await message.answer("Порт protected. Потрібен force або !")
        return

    try:
        sw["device"].down(interface)
        await message.answer("Порт вимкнено")
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


@dp.message(Command("access"))
@auth_required
async def access_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer("Використання: /access <switch> <alias> <vlan> [force]")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    alias = parts[2]
    vlan = parts[3]
    interface = sw["interfaces"].get(alias)
    if not interface:
        await message.answer("Невідомий порт")
        return

    if alias in sw["protected"] and not has_force_flag(message.text):
        await message.answer("Порт protected. Потрібен force або !")
        return

    try:
        output = sw["device"].set_access_vlan(interface, vlan)
        await message.answer(trim_output(output))
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


@dp.message(Command("trunk"))
@auth_required
async def trunk_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer("Використання: /trunk <switch> <alias> <vlan> [force]")
        return

    sw = get_switch(parts[1])
    if not sw:
        await message.answer("Невідомий свич")
        return

    alias = parts[2]
    vlan = parts[3]
    interface = sw["interfaces"].get(alias)
    if not interface:
        await message.answer("Невідомий порт")
        return

    if alias in sw["protected"] and not has_force_flag(message.text):
        await message.answer("Порт protected. Потрібен force або !")
        return

    try:
        output = sw["device"].add_trunk_vlan(interface, vlan)
        await message.answer(trim_output(output))
    except Exception as e:
        print(e)
        await message.answer("Помилка підключення до пристрою")


# ================= СТАРТ =================

async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
