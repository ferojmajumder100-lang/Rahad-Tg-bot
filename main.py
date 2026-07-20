#!/usr/bin/env python3
import requests
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
import time
import threading
import re
import json
import os
import uuid
import base64
import random
import sys
from datetime import datetime
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import pyotp

# ============================================================
# COLORFUL BUTTON SYSTEM (Style patch)
# ============================================================
_old_inline_dict = InlineKeyboardButton.to_dict
def _new_inline_dict(self):
    d = _old_inline_dict(self)
    if hasattr(self, 'style'):
        d['style'] = self.style
    if hasattr(self, 'custom_copy_text') and self.custom_copy_text:
        d['copy_text'] = {'text': str(self.custom_copy_text)}
        if 'callback_data' in d:
            del d['callback_data']
    return d
InlineKeyboardButton.to_dict = _new_inline_dict

_old_kb_dict = KeyboardButton.to_dict
def _new_kb_dict(self):
    d = _old_kb_dict(self)
    if hasattr(self, 'style'):
        d['style'] = self.style
    return d
KeyboardButton.to_dict = _new_kb_dict

def ibtn(text, callback_data=None, url=None, style=None, copy_text_str=None):
    kwargs = {'text': text}
    if copy_text_str:
        kwargs['callback_data'] = "fake_copy_btn"
    else:
        if callback_data: kwargs['callback_data'] = callback_data
        if url: kwargs['url'] = url
    b = InlineKeyboardButton(**kwargs)
    if style: b.style = style
    if copy_text_str: b.custom_copy_text = copy_text_str
    return b

def rbtn(text, style=None):
    b = KeyboardButton(text=text)
    if style: b.style = style
    return b
# ============================================================

# ==================== কনফিগারেশন ====================
TELEGRAM_TOKEN = "8399030537:AAGAWuVd0B59ninbr3U1KAbcnfBC-OvMoFY"
ADMIN_ID = 6314176381

COOKIE_DATR = "3XA5at-YBOFaGHi2xPrg-wka"
API_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
API_KEY = "M11OV849ED5"

HEADERS = {
    "mauthapi": API_KEY,
    "Content-Type": "application/json"
}

LOG_GROUP_ID = "-1003971229688"
OTP_GROUP_URL = "https://t.me/+eNEiopsvaqpkMTc1"

FRENCH_NAMES = [
    {"prenom":"Jean","nom":"Dupont"}, {"prenom":"Marie","nom":"Martin"},
    {"prenom":"Pierre","nom":"Durand"}, {"sophie":"Lefèvre","prenom":"Sophie","nom":"Lefèvre"},
    {"prenom":"Lucas","nom":"Moreau"}, {"prenom":"Emma","nom":"Petit"},
    {"prenom":"Louis","nom":"Roux"}, {"prenom":"Chloé","nom":"Richard"},
    {"prenom":"Hugo","nom":"Simon"}, {"prenom":"Inès","nom":"Laurent"}
]

# ==================== ডাটাবেস ====================
USER_DB = "users.json"
ACTIVE_NUMBERS_DB = "active_numbers.json"

_ENCODED_NAME = ""

def init_databases():
    files = {
        USER_DB: [],
        ACTIVE_NUMBERS_DB: {}
    }
    for file, default in files.items():
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump(default, f)

init_databases()

def get_all_users():
    with open(USER_DB, "r") as f:
        return json.load(f)

def add_user(user_id):
    with open(USER_DB, "r") as f:
        users = json.load(f)
    if user_id not in users:
        users.append(user_id)
        with open(USER_DB, "w") as f:
            json.dump(users, f)

def get_active_numbers():
    with open(ACTIVE_NUMBERS_DB, "r") as f:
        return json.load(f)

def save_active_numbers(numbers):
    with open(ACTIVE_NUMBERS_DB, "w") as f:
        json.dump(numbers, f)

def add_active_number(phone, chat_id, service, range_code):
    data = get_active_numbers()
    data[str(phone)] = {
        "chat_id": chat_id,
        "service": service,
        "range": range_code,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_active_numbers(data)

def remove_active_number(phone):
    data = get_active_numbers()
    if str(phone) in data:
        del data[str(phone)]
        save_active_numbers(data)

def mask_number(phone):
    phone_str = str(phone)
    if len(phone_str) >= 10:
        return phone_str[:7] + "XXX" + phone_str[-2:]
    return phone_str

def extract_otp_from_text(text):
    clean_text = re.sub(r'[-\s]', '', text)
    patterns = [
        r'\b(\d{8})\b', r'\b(\d{7})\b', r'\b(\d{6})\b',
        r'\b(\d{5})\b', r'\b(\d{4})\b', r'\b(\d{3})\b',
        r'code[:\s]*(\d+)', r'OTP[:\s]*(\d+)', r'(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match and len(match.group(1)) >= 3:
            return match.group(1)
    return "N/A"

def get_service_name_from_msg(msg):
    msg_lower = msg.lower()
    if 'facebook' in msg_lower: return "Facebook"
    elif 'whatsapp' in msg_lower: return "WhatsApp"
    elif 'instagram' in msg_lower: return "Instagram"
    return "Unknown"

def get_footer():
    try:
        decoded_name = base64.b64decode(_ENCODED_NAME).decode('utf-8')
        return f"\n\n━━━━━━━━━━━━━━━━━━━━\n{decoded_name.replace(':', '')}"
    except:
        return ""

def random_name():
    name = random.choice(FRENCH_NAMES)
    return name['prenom'], name['nom']

def random_birth():
    return random.randint(1, 28), random.randint(1, 12), random.randint(1980, 2005)

def clean_phone(phone):
    return re.sub(r'[^0-9]', '', phone)

def extract_numbers(text):
    numbers = re.findall(r'\d+', text)
    return [num for num in numbers if len(num) >= 4]

# ==================== FACEBOOK ACCOUNT CREATOR ====================
def create_facebook_account(phone, password):
    fname, lname = random_name()
    day, month, year = random_birth()
    phone = clean_phone(phone)
    
    android_ua = "Mozilla/5.0 (Linux; Android 12; itel S665L Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.91 Mobile Safari/537.36"
    headers = {
        'User-Agent': android_ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Android WebView";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'x-response-format': 'JSONStream',
        'sec-ch-ua-mobile': '?1',
        'x-asbd-id': '359341',
        'x-fb-lsd': 'AdRCh7SdER7Za5PotUuics5fFt0',
        'x-requested-with': 'XMLHttpRequest',
        'origin': 'https://limited.facebook.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://limited.facebook.com/reg/?is_two_steps_login=0&cid=103&refsrc=deprecated&soft=hjk',
        'priority': 'u=1, i',
        'Cookie': f'datr={COOKIE_DATR}'
    }
    
    data = {
        'ccp': '2', 'reg_instance': COOKIE_DATR, 'submission_request': 'true', 'helper': '',
        'reg_impression_id': str(uuid.uuid4()), 'ns': '1', 'zero_header_af_client': '',
        'app_id': '103', 'logger_id': str(uuid.uuid4()), 'field_names[0]': 'firstname',
        'firstname': fname, 'lastname': lname, 'field_names[1]': 'birthday_wrapper',
        'birthday_day': str(day), 'birthday_month': str(month), 'birthday_year': str(year),
        'age_step_input': '', 'did_use_age': 'false', 'field_names[2]': 'reg_email__',
        'reg_email__': phone, 'field_names[3]': 'sex', 'sex': '2', 'preferred_pronoun': '',
        'custom_gender': '', 'reg_passwd__': password, 'name_suggest_elig': 'false',
        'was_shown_name_suggestions': 'false', 'did_use_suggested_name': 'false',
        'use_custom_gender': 'false', 'guid': '', 'pre_form_step': '', 'submit': 'Sign up',
        'fb_dtsg': 'NAfx5UxG44eai86HC1iwiixBs1mUDFhn3ccN1fj3-SJJc64TeUsEAEg:0:0', 'jazoest': '24748',
        'lsd': 'AdRCh7SdER7Za5PotUuics5fFt0', '__dyn': '1Z3pawlEnwm8_Bg9ppoW5UdE4a2i5U4e0C86u7E39x60zU3ex608ewk9E4W0pKq0FE6S0x81vohw73wGwcq1GwqU2YwbK0oi0zE1jU1soG0hi0Lo6-0Co1kU1UU3jwea',
        '__csr': '', '__hsdp': '', '__hblp': '', '__sjsp': '', '__req': 'g', '__fmt': '1',
        '__a': 'AYzJ_41FhHOHmeaJtz_y-NZ41BrpCkk8MZbenM7ATpRLY9c4d3QLNQW9sph6SN5jNJBH5tH1yvE_P-EybRqM6tZ_nqLEaV4b3ZU', '__user': '0'
    }
    
    url = 'https://limited.facebook.com/reg/submit/?privacy_mutation_token=eyJ0eXBlIjowLCJjcmVhdGlvbl90aW1lIjoxNzgyMTQ5MzY4LCJjYWxsc2l0ZV9pZCI6OTA3OTI0NDAyOTQ4MDU4fQ%3D%3D&app_id=103&multi_step_form=1&skip_suma=0&shouldForceMTouch=1'
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, data=data, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200 and elapsed_time >= 1:
            cookies_dict = response.cookies.get_dict()
            if 'c_user' in cookies_dict:
                uid = cookies_dict['c_user']
                cookie_parts = []
                for key in ['datr', 'sb', 'ps_l', 'ps_n', 'm_pixel_ratio', 'wd', 'c_user', 'fr', 'xs']:
                    if key in cookies_dict:
                        cookie_parts.append(f"{key}={cookies_dict[key].replace(' ', '')}")
                    elif key == 'datr' and key not in cookies_dict:
                        cookie_parts.append(f"datr={COOKIE_DATR}")
                cookie_string = "; ".join(cookie_parts)
                return {
                    'success': True, 'uid': uid, 'name': f"{fname} {lname}",
                    'cookies': cookie_string, 'password': password, 'phone': phone
                }
            else:
                return {'success': False, 'error': 'No c_user in cookies'}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ==================== API FUNCTIONS ====================
def voltx_get_live_services():
    url = f"{API_BASE_URL}/liveaccess"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if res.status_code == 200:
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                services = data.get("data", {}).get("services", [])
                if services: return services
    except Exception as e:
        print(f"Error loading live services: {e}")
    return [
        {"sid": "Facebook", "ranges": ["8801XXX", "22501XXX"]},
        {"sid": "WhatsApp", "ranges": ["8801XXX", "447XXX"]}
    ]

def voltx_get_ranges_for_service(service_name):
    services = voltx_get_live_services()
    for s in services:
        if s.get("sid", "").lower() == service_name.lower():
            ranges = s.get("ranges", [])
            if ranges: return ranges
    return ["8801XXX", "22501XXX"]

def voltx_fetch_number(range_code):
    rid = range_code.replace("XXX", "").replace("X", "").strip()
    if not rid: rid = "8801"
    url = f"{API_BASE_URL}/getnum"
    payload = {"rid": rid}
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=30, verify=False)
        if res.status_code == 200:
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                number_data = data.get("data", {})
                full_number = number_data.get("full_number") or number_data.get("no_plus_number")
                if full_number:
                    return str(full_number).replace("+", "").strip()
    except Exception as e:
        print(f"Error fetching number: {e}")
    return None

def voltx_fetch_single_number(range_code):
    number = voltx_fetch_number(range_code)
    return [number] if number else []

def voltx_check_otp():
    url = f"{API_BASE_URL}/success-otp"
    results = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if res.status_code == 200:
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                otps = data.get("data", {}).get("otps", [])
                active = get_active_numbers()
                for phone in active:
                    for otp_item in otps:
                        otp_number = otp_item.get("number", "").replace("+", "").strip()
                        if phone == otp_number:
                            message = otp_item.get("message", "")
                            if message:
                                otp_code = extract_otp_from_text(message)
                                service_name = get_service_name_from_msg(message)
                                if service_name == "Unknown":
                                    service_name = active[phone].get("service", "Unknown")
                                if otp_code != "N/A":
                                    results.append({
                                        "phone": phone, "message": message,
                                        "otp": otp_code, "service": service_name,
                                    })
                                    break
    except Exception as e:
        print(f"Error checking OTP: {e}")
    return results

# ==================== KEYBOARDS ====================
def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(rbtn("🎲 GET NUMBER", "primary"), rbtn("🔐 2FA CODE", "success"))
    markup.row(rbtn("🔑 Set Password", "primary"), rbtn("🚀 Create Now", "success"))
    markup.row(rbtn("📩 CONTACT ADMIN", "primary"), rbtn("⏹ Stop", "danger"))
    return markup

def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(rbtn("📢 Broadcast", "primary"), rbtn("📊 Stats", "success"))
    markup.row(rbtn("🔙 Back Main Menu", "danger"))
    return markup

def get_service_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    services = voltx_get_live_services()
    for s in services[:4]:
        sid = s.get("sid", "Unknown")
        markup.add(ibtn(f"📘 {sid}", callback_data=f"service_{sid.lower()}", style="primary"))
    markup.row(ibtn("🔄 Refresh Services", callback_data="refresh_services", style="success"))
    markup.row(ibtn("🔙 Back Main Menu", callback_data="back_main_menu", style="danger"))
    return markup

# 240+ COUNTRY MAP DATA SYSTEM
COUNTRY_MAP = {
    "93": ("🇦🇫", "Afghanistan"), "355": ("🇦🇱", "Albania"), "213": ("🇩🇿", "Algeria"), "1684": ("🇦🇸", "American Samoa"), 
    "376": ("🇦🇩", "Andorra"), "244": ("🇦☉", "Angola"), "1264": ("🇦🇮", "Anguilla"), "1268": ("🇦🇬", "Antigua & Barbuda"), 
    "54": ("🇦🇷", "Argentina"), "374": ("🇦🇲", "Armenia"), "297": ("🇦🇼", "Aruba"), "61": ("🇦🇺", "Australia"), 
    "43": ("🇦🇹", "Austria"), "994": ("🇦🇿", "Azerbaijan"), "1242": ("🇧🇸", "Bahamas"), "973": ("🇧🇭", "Bahrain"), 
    "880": ("🇧🇩", "Bangladesh"), "1246": ("🇧🇧", "Barbados"), "375": ("🇧🇾", "Belarus"), "32": ("🇧🇪", "Belgium"), 
    "501": ("🇧🇿", "Belize"), "229": ("🇧🇯", "Benin"), "1441": ("🇧🇲", "Bermuda"), "975": ("🇧🇹", "Bhutan"), 
    "591": ("🇧🇴", "Bolivia"), "387": ("🇧🇦", "Bosnia"), "267": ("🇧🇼", "Botswana"), "55": ("🇧🇷", "Brazil"), 
    "1284": ("🇻🇬", "British Virgin Islands"), "673": ("🇧🇳", "Brunei"), "359": ("🇧🇬", "Bulgaria"), "226": ("🇧🇫", "Burkina Faso"), 
    "257": ("🇧🇮", "Burundi"), "238": ("🇨🇻", "Cape Verde"), "855": ("🇰🇭", "Cambodia"), "237": ("🇨🇲", "Cameroon"), 
    "2376": ("🇨🇲", "Cameroon"), "1": ("🇺🇸", "United States/Canada"), "1345": ("🇰🇾", "Cayman Islands"), 
    "236": ("🇨🇫", "Central African Republic"), "235": ("🇹🇩", "Chad"), "56": ("🇨🇱", "Chile"), "86": ("🇨🇳", "China"), 
    "57": ("🇨🇴", "Colombia"), "269": ("🇰🇲", "Comoros"), "242": ("🇨🇬", "Congo"), "243": ("🇨🇩", "DR Congo"), 
    "682": ("🇨🇰", "Cook Islands"), "506": ("🇨🇷", "Costa Rica"), "225": ("🇨🇮", "Ivory Coast"), "2250": ("🇨🇮", "Ivory Coast"), 
    "385": ("🇭🇷", "Croatia"), "53": ("🇨🇺", "Cuba"), "357": ("🇨🇾", "Cyprus"), "420": ("🇨🇿", "Czechia"), 
    "45": ("🇩🇰", "Denmark"), "253": ("🇩🇯", "Djibouti"), "1767": ("🇩🇲", "Dominica"), "1809": ("🇩🇴", "Dominican Republic"), 
    "1829": ("🇩🇴", "Dominican Republic"), "1849": ("🇩🇴", "Dominican Republic"), "593": ("🇪🇨", "Ecuador"), 
    "20": ("🇪🇬", "Egypt"), "503": ("🇸🇻", "El Salvador"), "240": ("🇬🇶", "Equatorial Guinea"), "291": ("🇪🇷", "Eritrea"), 
    "372": ("🇪🇪", "Estonia"), "251": ("🇪🇹", "Ethiopia"), "1340": ("🇻🇮", "US Virgin Islands"), "500": ("🇫🇰", "Falkland Islands"), 
    "298": ("🇫🇴", "Faroe Islands"), "679": ("🇫يج", "Fiji"), "358": ("🇫🇮", "Finland"), "33": ("🇫🇷", "France"), 
    "594": ("🇬🇫", "French Guiana"), "689": ("🇵🇫", "French Polynesia"), "241": ("🇬🇦", "Gabon"), "220": ("🇬🇲", "Gambia"), 
    "995": ("🇬🇪", "Georgia"), "49": ("🇩🇪", "Germany"), "233": ("🇬🇭", "Ghana"), "350": ("🇬🇮", "Gibraltar"), 
    "30": ("🇬🇷", "Greece"), "299": ("🇬🇱", "Greenland"), "1473": ("🇬🇩", "Grenada"), "590": ("🇬🇵", "Guadeloupe"), 
    "1671": ("🇬🇺", "Guam"), "502": ("🇬🇹", "Guatemala"), "224": ("🇬🇳", "Guinea"), "245": ("🇬🇼", "Guinea-Bissau"), 
    "592": ("🇬🇾", "Guyana"), "509": ("🇭🇹", "Haiti"), "504": ("🇭🇳", "Honduras"), "852": ("🇭🇰", "Hong Kong"), 
    "36": ("🇭🇺", "Hungary"), "354": ("🇮🇸", "Iceland"), "91": ("🇮🇳", "India"), "62": ("🇮🇩", "Indonesia"), 
    "98": ("🇮🇷", "Iran"), "964": ("🇮🇶", "Iraq"), "353": ("🇮🇪", "Ireland"), "972": ("🇮🇱", "Israel"), 
    "39": ("🇮🇹", "Italy"), "1876": ("🇯🇲", "Jamaica"), "81": ("🇯🇵", "Japan"), "962": ("🇯🇴", "Jordan"), 
    "7": ("🇷🇺", "Russia/Kazakhstan"), "254": ("🇰🇪", "Kenya"), "686": ("🇰🇮", "Kiribati"), "965": ("🇰🇼", "Kuwait"), 
    "996": ("🇰🇬", "Kyrgyzstan"), "856": ("🇱🇦", "Laos"), "371": ("🇱🇻", "Latvia"), "961": ("🇱🇧", "Lebanon"), 
    "266": ("🇱🇸", "Lesotho"), "231": ("🇱🇷", "Liberia"), "218": ("🇱🇾", "Libya"), "423": ("🇱🇮", "Liechtenstein"), 
    "370": ("🇱🇹", "Lithuania"), "352": ("🇱🇺", "Luxembourg"), "853": ("🇲🇴", "Macao"), "389": ("🇲🇰", "North Macedonia"), 
    "261": ("🇲🇬", "Madagascar"), "2613": ("🇲🇬", "Madagascar"), "265": ("🇲🇼", "Malawi"), "60": ("🇲🇾", "Malaysia"), 
    "960": ("🇲🇻", "Maldives"), "223": ("🇲🇱", "Mali"), "356": ("🇲🇹", "Malta"), "692": ("🇲🇭", "Marshall Islands"), 
    "596": ("🇲🇶", "Martinique"), "222": ("🇲🇷", "Mauritania"), "230": ("🇲🇺", "Mauritius"), "262": ("🇾🇹", "Mayotte"), 
    "52": ("🇲🇽", "Mexico"), "691": ("🇫🇲", "Micronesia"), "373": ("🇲🇩", "Moldova"), "377": ("🇲🇨", "Monaco"), 
    "976": ("🇲🇳", "Mongolia"), "382": ("🇲 Montenegro"), "1664": ("🇲🇸", "Montserrat"), "212": ("🇲🇦", "Morocco"), 
    "258": ("🇲🇿", "Mozambique"), "95": ("🇲🇲", "Myanmar"), "264": ("🇳🇦", "Namibia"), "674": ("🇳🇷", "Nauru"), 
    "977": ("🇳🇵", "Nepal"), "31": ("🇳🇱", "Netherlands"), "687": ("🇳🇨", "New Caledonia"), "64": ("🇳🇿", "New Zealand"), 
    "505": ("🇳🇮", "Nicaragua"), "227": ("🇳🇪", "Niger"), "234": ("🇳🇬", "Nigeria"), "683": ("🇳🇺", "Niue"), 
    "1670": ("🇲🇵", "Northern Mariana Islands"), "47": ("🇳🇴", "Norway"), "968": ("🇴🇲", "Oman"), "92": ("🇵🇰", "Pakistan"), 
    "680": ("🇵🇼", "Palau"), "970": ("🇵🇸", "Palestine"), "507": ("🇵🇦", "Panama"), "675": ("🇵🇬", "Papua New Guinea"), 
    "595": ("🇵🇾", "Paraguay"), "51": ("🇵🇪", "Peru"), "63": ("🇵🇭", "Philippines"), "48": ("🇵🇱", "Poland"), 
    "351": ("🇵🇹", "Portugal"), "1787": ("🇵🇷", "Puerto Rico"), "1939": ("🇵🇷", "Puerto Rico"), "974": ("🇶🇦", "Qatar"), 
    "40": ("🇷🇴", "Romania"), "4077": ("🇷🇴", "Romania"), "250": ("🇷🇼", "Rwanda"), "290": ("🇸🇭", "Saint Helena"), 
    "1869": ("🇰🇳", "Saint Kitts & Nevis"), "1758": ("🇱🇨", "Saint Lucia"), "1784": ("🇻🇨", "Saint Vincent"), 
    "685": ("🇼🇸", "Samoa"), "378": ("🇸🇲", "San Marino"), "239": ("🇸🇹", "Sao Tome & Principe"), "966": ("🇸🇦", "Saudi Arabia"), 
    "221": ("🇸🇳", "Senegal"), "381": ("🇷🇸", "Serbia"), "248": ("🇸🇨", "Seychelles"), "232": ("🇸🇱", "Sierra Leone"), 
    "65": ("🇸🇬", "Singapore"), "421": ("🇸🇰", "Slovakia"), "386": ("🇸🇮", "Slovenia"), "677": ("🇸🇧", "Solomon Islands"), 
    "252": ("🇸☉", "Somalia"), "27": ("🇿🇦", "South Africa"), "82": ("🇰🇷", "South Korea"), "211": ("🇸🇸", "South Sudan"), 
    "34": ("🇪🇸", "Spain"), "94": ("🇱💖", "Sri Lanka"), "249": ("🇸🇩", "Sudan"), "597": ("🇸🇷", "Suriname"), 
    "268": ("🇸🇿", "Eswatini"), "46": ("🇸🇪", "Sweden"), "41": ("🇨🇭", "Switzerland"), "963": ("🇸🇾", "Syria"), 
    "886": ("🇹🇼", "Taiwan"), "992": ("🇹🇯", "Tajikistan"), "255": ("🇹🇿", "Tanzania"), "66": ("🇹🇭", "Thailand"), 
    "228": ("🇹🇬", "Togo"), "690": ("🇹🇰", "Tokelau"), "676": ("🇹🇴", "Tonga"), "1868": ("🇹🇹", "Trinidad & Tobago"), 
    "216": ("🇹🇳", "Tunisia"), "90": ("🇹🇷", "Turkey"), "993": ("🇹🇲", "Turkmenistan"), "1649": ("🇹🇨", "Turks & Caicos Islands"), 
    "688": ("🇹🇻", "Tuvalu"), "256": ("🇺🇬", "Uganda"), "380": ("🇺🇦", "Ukraine"), "971": ("🇦🇪", "United Arab Emirates"), 
    "44": ("🇬🇧", "United Kingdom"), "598": ("🇺🇾", "Uruguay"), "998": ("🇺🇿", "Uzbekistan"), "678": ("🇻🇺", "Vanuatu"), 
    "58": ("🇻🇪", "Venezuela"), "84": ("🇻🇳", "Vietnam"), "681": ("🇼🇫", "Wallis & Futuna"), "967": ("🇾🇪", "Yemen"), 
    "260": ("🇿🇲", "Zambia"), "263": ("🇿🇼", "Zimbabwe")
}

def get_country_info(range_code):
    digits = re.sub(r'[^0-9]', '', range_code)
    for length in (4, 3, 2, 1):
        prefix = digits[:length]
        if prefix in COUNTRY_MAP: return COUNTRY_MAP[prefix]
    return ("📱", "")

def get_range_keyboard(ranges, service):
    markup = InlineKeyboardMarkup(row_width=2)
    for r in ranges[:10]:
        flag, country = get_country_info(r)
        label = f"{flag} {r} {country}" if country else f"📱 {r}"
        markup.add(ibtn(label, callback_data=f"get_number_{service}_{r}", style="primary"))
    markup.row(ibtn("🔄 Refresh", callback_data=f"refresh_ranges_{service}", style="success"))
    markup.row(ibtn("🔙 Back to Services", callback_data="back_to_services", style="danger"))
    return markup

def get_fb_creator_range_keyboard(ranges):
    markup = InlineKeyboardMarkup(row_width=2)
    for r in ranges[:12]:
        flag, country = get_country_info(r)
        label = f"{flag} {r} {country}" if country else f"📱 {r}"
        markup.add(ibtn(label, callback_data=f"fbcreate_{r}", style="primary"))
    markup.row(ibtn("🔙 Back Main Menu", callback_data="back_main_menu", style="danger"))
    return markup

def get_2fa_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(rbtn("🔄 Regenerate", "success"))
    markup.row(rbtn("🔙 Back Main Menu", "danger"))
    return markup

# ==================== NOTIFICATIONS ====================
def send_otp_notification(chat_id, phone, service, otp, message):
    masked = mask_number(phone)
    footer = get_footer()
    active = get_active_numbers()
    range_code = active.get(str(phone), {}).get("range", None)
    country_line = range_line = ""
    if range_code:
        flag, country_name = get_country_info(range_code)
        country_line = f"\n🌍 Country : {flag} {country_name}" if country_name else f"\n🌍 Country : {flag}"
        range_line = f"\n🌀 Range : `{range_code}`"

    dm_msg = f"✅ OTP RECEIVED!\n━━━━━━━━━━━━━━━━━━━━\n📱 Number: `{phone}`\n🎯 Service: {service}{country_line}{range_line}\n━━━━━━━━━━━━━━━━━━━━\n🔐 OTP Code: `{otp}`\n━━━━━━━━━━━━━━━━━━━━\n📩 Full SMS:\n`{message[:200]}`{footer}"
    group_msg = f"✅ OTP RECEIVED!\n━━━━━━━━━━━━━━━━━━━━\n📱 Number: `{masked}`\n🎯 Service: {service}{country_line}{range_line}\n━━━━━━━━━━━━━━━━━━━━\n🔐 OTP Code: `{otp}`\n━━━━━━━━━━━━━━━━━━━━\n📩 Full SMS:\n`{message[:200]}`{footer}"
    
    otp_markup = InlineKeyboardMarkup(row_width=1)
    otp_markup.row(ibtn(f"📋 {otp} (OTP Copy)", copy_text_str=str(otp), style="success"))
    otp_markup.row(ibtn("💬 OTP GROUP 🔗", url=OTP_GROUP_URL, style="primary"))
    try:
        bot.send_message(chat_id, dm_msg, parse_mode="Markdown", reply_markup=otp_markup)
        bot.send_message(LOG_GROUP_ID, group_msg, parse_mode="Markdown")
    except Exception as e: print(f"Send error: {e}")

def send_number_received_notification(chat_id, numbers, service_name, range_code=None):
    for number in numbers:
        country_line = range_line = ""
        if range_code:
            flag, country_name = get_country_info(range_code)
            country_line = f"\n🌍 Country : {flag} {country_name}" if country_name else f"\n🌍 Country : {flag}"
            range_line = f"\n🌀 Range : `{range_code}`"

        markup = InlineKeyboardMarkup(row_width=1)
        markup.row(ibtn(f"📋 {number} (Tap to Copy)", copy_text_str=number, style="primary"))
        markup.row(ibtn("🔄 Change Number", callback_data=f"change_number_{service_name}", style="success"))
        markup.row(ibtn("🌍 Change Country", callback_data=f"back_to_ranges", style="primary"))
        markup.row(ibtn("💬 OTP GROUP 🔗", url=OTP_GROUP_URL, style="primary"))

        msg = f"🎯 NEW NUMBER RECEIVED!\n━━━━━━━━━━━━━━━━━━━━\n📱 Number: `{number}`\n🎯 Service: {service_name}{country_line}{range_line}\n━━━━━━━━━━━━━━━━━━━━\n💡 OTP will appear here automatically!\n\n👆 নাম্বার বাটনে চাপ দিলে কপি হবে!"
        bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=markup)

# ==================== BOT ENGINE & STATE ====================
bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_service = {}
user_last_range = {}
user_data_store = {}
bot_states = {}

@bot.message_handler(commands=['start'])
def start_cmd(message):
    add_user(message.chat.id)
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👋 Welcome Admin!", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(
            message.chat.id,
            f"✨ Welcome {message.from_user.first_name}! ✨\n\n"
            f"🤖 <b>ARAFAAT FB Creator + VOLTX OTP System</b>\n\n"
            f"📌 <b>কিভাবে ব্যবহার করবেন (Auto Creator):</b>\n"
            f"1️⃣ প্রথমে '🔑 Set Password' বাটনে ক্লিক করে পাসওয়ার্ড সেট করুন।\n"
            f"2️⃣ এরপর '🚀 Create Now' বাটনে চাপ দিয়ে কাঙ্ক্ষিত লাইভ রেঞ্জ সিলেক্ট করুন।\n"
            f"3️⃣ কয়টি অ্যাকাউন্ট তৈরি করবেন তা ইনপুট দিন (সর্বোচ্চ ৫)।\n"
            f"4️⃣ বোট স্বয়ংক্রিয়ভাবে নাম্বার তুলে রিয়াল-টাইম একাউন্ট তৈরি করে কুকি সহ তথ্য দিয়ে দেবে।",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🔧 Admin Panel", reply_markup=get_admin_keyboard())

# ==================== CALLBACK CODES ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    
    if data in ["approve_", "reject_", "reply_"] or data.startswith("approve_") or data.startswith("reject_") or data.startswith("reply_"):
        admin_callback(call)
        return

    if data == "back_main_menu":
        bot.answer_callback_query(call.id)
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        bot.send_message(chat_id, "🏠 Main Menu", reply_markup=get_main_keyboard())
        return
    
    if data == "back_to_services":
        bot.edit_message_text("🔍 Select Service:", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data == "back_to_ranges":
        service_name = user_service.get(chat_id, "facebook")
        ranges = voltx_get_ranges_for_service(service_name)
        bot.answer_callback_query(call.id)
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        if ranges:
            bot.send_message(chat_id, f"🔥 Live Ranges for {service_name.capitalize()}:", reply_markup=get_range_keyboard(ranges, service_name))
        else:
            bot.send_message(chat_id, "❌ No live ranges found!", reply_markup=get_service_keyboard())
        return
    
    if data == "refresh_services":
        bot.edit_message_text("🔍 Select Service:", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("refresh_ranges_"):
        service_name = data.replace("refresh_ranges_", "")
        ranges = voltx_get_ranges_for_service(service_name)
        if ranges:
            bot.edit_message_text(f"🔥 Live Ranges for {service_name.capitalize()} (Refreshed):", chat_id, msg_id, reply_markup=get_range_keyboard(ranges, service_name))
        else:
            bot.edit_message_text("❌ No live ranges found!", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("service_"):
        service_name = data.replace("service_", "")
        user_service[chat_id] = service_name
        ranges = voltx_get_ranges_for_service(service_name)
        if ranges:
            bot.edit_message_text(f"🔥 Live Ranges for {service_name.capitalize()}:", chat_id, msg_id, reply_markup=get_range_keyboard(ranges, service_name))
        else:
            bot.edit_message_text(f"❌ No live ranges found!", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("get_number_"):
        parts = data.split("_")
        service_name = parts[2]
        range_code = parts[3]
        user_last_range[chat_id] = range_code
        user_service[chat_id] = service_name
        
        bot.edit_message_text(f"⏳ Requesting 1 number from `{range_code}`...\n\nPlease wait...", chat_id, msg_id, parse_mode="Markdown")
        numbers_found = voltx_fetch_single_number(range_code)
        if numbers_found:
            for number in numbers_found:
                add_active_number(number, chat_id, service_name.capitalize(), range_code)
            bot.delete_message(chat_id, msg_id)
            send_number_received_notification(chat_id, numbers_found, service_name.capitalize(), range_code)
        else:
            bot.edit_message_text(f"❌ No numbers available from `{range_code}`!\n\nPlease try another range.", chat_id, msg_id, parse_mode="Markdown", reply_markup=get_range_keyboard(voltx_get_ranges_for_service(service_name), service_name))
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("change_number_"):
        service_name = data.replace("change_number_", "")
        range_code = user_last_range.get(chat_id)
        if not range_code:
            bot.answer_callback_query(call.id, "Select range first!", show_alert=True)
            return
        bot.delete_message(chat_id, msg_id)
        loading_msg = bot.send_message(chat_id, f"⏳ Requesting 1 new number from `{range_code}`...\n\nPlease wait...", parse_mode="Markdown")
        numbers_found = voltx_fetch_single_number(range_code)
        bot.delete_message(chat_id, loading_msg.message_id)
        if numbers_found:
            for number in numbers_found:
                add_active_number(number, chat_id, service_name, range_code)
            send_number_received_notification(chat_id, numbers_found, service_name, range_code)
        else:
            bot.send_message(chat_id, f"❌ No numbers available from `{range_code}`!\n\nPlease try another range.", parse_mode="Markdown", reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return

    # ==================== NEW FB CREATOR VIA RANGE CALLBACK ====================
    if data.startswith("fbcreate_"):
        bot.answer_callback_query(call.id)
        selected_range = data.replace("fbcreate_", "")
        if chat_id not in bot_states:
            bot_states[chat_id] = {}
        bot_states[chat_id]['selected_fb_range'] = selected_range
        
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        
        msg = bot.send_message(
            chat_id,
            f"🎯 <b>নির্বাচিত রেঞ্জ:</b> <code>{selected_range}</code>\n\n"
            "🔢 <b>কয়টি অ্যাকাউন্ট তৈরি করতে চান? (সর্বোচ্চ ৫টি):</b>\n"
            "১ থেকে ৫ এর মধ্যে যেকোনো একটি সংখ্যা লিখে ইনপুট দিন।",
            parse_mode='HTML'
        )
        bot_states[chat_id]['waiting_for_account_count'] = True
        return

# ==================== CONTROLLER & TEXT CODES ====================
@bot.message_handler(func=lambda m: True)
def handle_text_messages(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    if chat_id not in bot_states:
        bot_states[chat_id] = {}

    if text == "🔙 Back Main Menu":
        bot_states[chat_id] = {}
        if message.from_user.id == ADMIN_ID:
            bot.send_message(chat_id, "🏠 Main Menu", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(chat_id, "🏠 Main Menu", reply_markup=get_main_keyboard())
        return

    # Admin buttons routing
    if message.from_user.id == ADMIN_ID and text in ["📢 Broadcast", "📊 Stats"]:
        if text == "📢 Broadcast":
            msg = bot.send_message(chat_id, "📢 Send broadcast:")
            bot.register_next_step_handler(msg, broadcast_msg)
        elif text == "📊 Stats":
            users = len(get_all_users())
            active = len(get_active_numbers())
            bot.send_message(chat_id, f"📊 Stats\n👥 Users: {users}\n📱 Active: {active}")
        return

    if text == "🎲 GET NUMBER":
        bot.send_message(chat_id, "🔍 Select Service:", reply_markup=get_service_keyboard())
        return

    if text == "🔐 2FA CODE":
        msg = bot.send_message(chat_id, "🔐 Send 2FA Secret Key:\nExample: JBSWY3DPEHPK3PXP", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_2fa)
        return

    if text == "🔄 Regenerate":
        msg = bot.send_message(chat_id, "🔐 Send 2FA Secret Key:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_2fa)
        return

    if text == "📩 CONTACT ADMIN":
        msg = bot.send_message(chat_id, "📝 Write your message:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, forward_to_admin)
        return

    if text == "🔑 Set Password":
        bot.send_message(
            chat_id,
            "🔑 <b>Set Account Password</b>\n\nPlease send your desired password.\nPassword must be at least 6 characters.\n\nExample: MyPass@123",
            parse_mode='HTML', reply_markup=get_main_keyboard()
        )
        bot_states[chat_id]['waiting_for_password'] = True
        return

    if text == "⏹ Stop":
        bot_states[chat_id]['creating_mode'] = False
        bot_states[chat_id]['waiting_for_account_count'] = False
        bot.send_message(chat_id, "🛑 <b>Stopped creating accounts!</b>\n\nClick '🚀 Create Now' to start again.", parse_mode='HTML', reply_markup=get_main_keyboard())
        return

    # ==================== UPDATED "CREATE NOW" BUTTON TRIGGER ====================
    if text == "🚀 Create Now":
        if chat_id not in user_data_store or 'password' not in user_data_store[chat_id]:
            bot.send_message(chat_id, "⚠️ <b>Password Not Set!</b>\n\nPlease set a password first using '🔑 Set Password' button.", parse_mode='HTML', reply_markup=get_main_keyboard())
            return
        
        fb_ranges = voltx_get_ranges_for_service("facebook")
        if fb_ranges:
            bot.send_message(
                chat_id, 
                "📘 <b>Facebook Live Ranges:</b>\n\nঅ্যাকাউন্ট তৈরি করার জন্য নিচের যেকোনো একটি রেঞ্জ সিলেক্ট করুন। বোট স্বয়ংক্রিয়ভাবে নাম্বার তুলে কাজ শুরু করবে।", 
                parse_mode='HTML', 
                reply_markup=get_fb_creator_range_keyboard(fb_ranges)
            )
        else:
            bot.send_message(chat_id, "❌ No Facebook live ranges available at the moment!", reply_markup=get_main_keyboard())
        return

    # Handle Input Passwords
    if bot_states[chat_id].get('waiting_for_password'):
        if len(text) < 6:
            bot.send_message(chat_id, "⚠️ Password must be at least 6 characters!\nPlease try again.", reply_markup=get_main_keyboard())
            return
        if chat_id not in user_data_store:
            user_data_store[chat_id] = {}
        user_data_store[chat_id]['password'] = text
        bot_states[chat_id]['waiting_for_password'] = False
        bot.send_message(chat_id, f"✅ <b>Password Set Successfully!</b>\n\nPassword: <code>{text}</code>\n\nNow click '🚀 Create Now' to start creating accounts.", parse_mode='HTML', reply_markup=get_main_keyboard())
        return

    # ==================== HANDLE ACCOUNT COUNT & AUTO AUTOMATION TRIGGER ====================
    if bot_states[chat_id].get('waiting_for_account_count'):
        if not text.isdigit() or int(text) < 1 or int(text) > 5:
            bot.send_message(chat_id, "⚠️ দয়া করে ১ থেকে ৫ এর মধ্যে একটি সঠিক সংখ্যা ইনপুট দিন!", reply_markup=get_main_keyboard())
            return
        
        total_accounts_needed = int(text)
        bot_states[chat_id]['waiting_for_account_count'] = False
        bot_states[chat_id]['creating_mode'] = True
        
        range_code = bot_states[chat_id].get('selected_fb_range')
        password = user_data_store.get(chat_id, {}).get('password')
        
        bot.send_message(
            chat_id, 
            f"🚀 <b>Starting Auto Batch Creation...</b>\n\n"
            f"🌀 <b>Selected Range:</b> <code>{range_code}</code>\n"
            f"🔢 <b>Target Accounts:</b> {total_accounts_needed}\n\n"
            f"⚡ বোট এখন স্বয়ংক্রিয়ভাবে এপিআই থেকে নাম্বার তুলে অ্যাকাউন্ট তৈরি করা শুরু করছে। অনুগ্রহ করে নিচে রিয়াল-টাইম রিপোর্টের জন্য অপেক্ষা করুন:", 
            parse_mode='HTML'
        )

        # Multi-Thread Account Creator Engine logic mapped directly to auto-fetched numbers
        def single_account_creator(phone, index, total, user_pass, target_chat, results_tracker):
            if not bot_states.get(target_chat, {}).get('creating_mode', False):
                return

            processing_msg = bot.send_message(target_chat, f"⏳ <b>[Thread Active] Creating account {index}/{total}...</b>\n📱 Number: <code>{phone}</code>\n\n⏳ Please wait...", parse_mode='HTML')
            result = create_facebook_account(phone, user_pass)
            
            if result.get('success'):
                results_tracker['success'] += 1
                account_text = (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ <b>ACCOUNT #{index} - CREATED!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📱 <b>Number:</b>\n"
                    f"<code>{result['phone']}</code>\n\n"
                    f"🆔 <b>UID:</b>\n"
                    f"<code>{result['uid']}</code>\n\n"
                    f"👤 <b>Name:</b>\n"
                    f"<code>{result['name']}</code>\n\n"
                    f"🔑 <b>Password:</b>\n"
                    f"<code>{result['password']}</code>\n\n"
                    f"🍪 <b>Cookies:</b>\n"
                    f"<code>{result['cookies']}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 Progress: Complete"
                )
                bot.edit_message_text(account_text, target_chat, processing_msg.message_id, parse_mode='HTML')
            else:
                results_tracker['failed'] += 1
                error = result.get('error', 'Unknown error')
                bot.edit_message_text(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ <b>ACCOUNT #{index} - FAILED!</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📱 Number: <code>{phone}</code>\n❌ Error: {error}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━", target_chat, processing_msg.message_id, parse_mode='HTML')

        def auto_fetch_and_schedule_batch(target_chat, fb_range, count, user_pass):
            tracker = {'success': 0, 'failed': 0}
            
            for i in range(1, count + 1):
                if not bot_states.get(target_chat, {}).get('creating_mode', False):
                    break
                
                status_msg = bot.send_message(target_chat, f"⏳ <b>[{i}/{count}] Requesting number from API for range `{fb_range}`...</b>", parse_mode='HTML')
                fetched_num = voltx_fetch_number(fb_range)
                bot.delete_message(target_chat, status_msg.message_id)
                
                if not fetched_num:
                    bot.send_message(target_chat, f"❌ <b>[{i}/{count}] Failed to fetch number from range `{fb_range}`!</b> Skipping...", parse_mode='HTML')
                    tracker['failed'] += 1
                    continue
                
                # Active DB তে নাম্বারটি যুক্ত করা হচ্ছে যাতে OTP ক্যাচ করতে পারে
                add_active_number(fetched_num, target_chat, "Facebook", fb_range)
                
                # ব্যাকগ্রাউন্ড থ্রেডে অ্যাকাউন্ট ক্রিয়েশন রান করা হচ্ছে 
                t = threading.Thread(
                    target=single_account_creator, 
                    args=(fetched_num, i, count, user_pass, target_chat, tracker)
                )
                t.start()
                t.join() # প্রতিটি অ্যাকাউন্ট সিকোয়েন্সিয়ালি প্রসেস করার জন্য ওয়েট করবে 
                time.sleep(1.5)

            summary_text = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 <b>BATCH CREATION COMPLETE!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Summary:</b>\n"
                f"📱 Total Requested: {count}\n"
                f"✅ Success: {tracker['success']}\n"
                f"❌ Failed: {tracker['failed']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏠 Click '🚀 Create Now' to launch another batch."
            )
            bot.send_message(target_chat, summary_text, parse_mode='HTML', reply_markup=get_main_keyboard())

        # মাস্টার ব্যাকগ্রাউন্ড শিডিউলার রান করা হচ্ছে
        threading.Thread(
            target=auto_fetch_and_schedule_batch, 
            args=(chat_id, range_code, total_accounts_needed, password), 
            daemon=True
        ).start()
        return

    bot.send_message(chat_id, "ℹ️ Please use the buttons below to get started!", reply_markup=get_main_keyboard())

# ==================== STEP FUNCTIONS FOR HANDLERS ====================
def forward_to_admin(message):
    if message.text:
        markup = InlineKeyboardMarkup()
        markup.row(ibtn("💬 Reply", callback_data=f"reply_{message.chat.id}", style="primary"))
        bot.send_message(ADMIN_ID, f"📩 New Message from {message.from_user.first_name}\nID: {message.chat.id}\n\n{message.text}", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ Message sent to admin!")

def process_2fa(message):
    secret = message.text.strip().replace(" ", "")
    try:
        totp = pyotp.TOTP(secret)
        otp = totp.now()
        bot.send_message(message.chat.id, f"🔐 Your 2FA Code:\n\n`{otp}`", parse_mode="Markdown", reply_markup=get_2fa_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ Invalid Secret Key!", reply_markup=get_main_keyboard())

def broadcast_msg(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 Broadcast\n\n{message.text}")
            success += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Sent to {success} users!")

def admin_callback(call):
    if call.data.startswith("reply_"):
        user_id = int(call.data.split("_")[1])
        msg = bot.send_message(call.message.chat.id, f"✍️ Reply to {user_id}:")
        bot.register_next_step_handler(msg, send_reply, user_id)
        bot.answer_callback_query(call.id)

def send_reply(message, user_id):
    try:
        bot.send_message(user_id, f"👨‍💻 Admin Reply:\n\n{message.text}")
        bot.send_message(message.chat.id, "✅ Reply sent!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed: {e}")

# ==================== OTP MONITOR LOOP ====================
sent_otps = set()

def otp_monitor():
    global sent_otps
    print("🔄 OTP Monitor Loop Thread Active")
    while True:
        try:
            otps = voltx_check_otp()
            for otp_data in otps:
                phone = otp_data["phone"]
                unique_key = f"{phone}_{otp_data['otp']}"
                if unique_key not in sent_otps:
                    sent_otps.add(unique_key)
                    active = get_active_numbers()
                    if str(phone) in active:
                        chat_id = active[str(phone)]["chat_id"]
                        send_otp_notification(chat_id, phone, otp_data["service"], otp_data["otp"], otp_data["message"])
                        remove_active_number(phone)
            if len(sent_otps) > 2000:
                sent_otps.clear()
        except Exception as e:
            print(f"Monitor Error: {e}")
        time.sleep(5)

# ==================== MAIN CORE ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 COMBINED ARAFAAT SYSTEM + VOLTX OTP BOT ENGINE")
    print("🚀 Auto Verification Hook Enabled: Auto Fetch Numbers")
    print("⚙️ Thread Pool Batch Optimization Configured!")
    print("=" * 60)
    
    # Start monitor thread
    threading.Thread(target=otp_monitor, daemon=True).start()
    
    print("✅ System Core Synchronized Successfully!")
    bot.infinity_polling(timeout=60)
