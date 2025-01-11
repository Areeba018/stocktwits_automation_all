
import asyncio
import os
import time
import random
import string
import json
import traceback
import httpx
import requests

from dotenv import load_dotenv

from common.database_v2 import make_connection, make_engine
from common.gdb_helper_v2 import GDBHelper
from common.helpers import MakeTimedUniqueId
from modules.application.models import Profile, Account

from stocktwits.stocktwits import Stocktwits
from namecheap import NamecheapApi

from redbox import EmailBox
from redbox.query import UNSEEN, SUBJECT

from bs4 import BeautifulSoup


def generate_random_user():
    """
    Generate a random username.
    Format: [Adjective][Noun][RandomNumber]
    """
    adjectives = ["Swift", "Happy", "Brave", "Cool", "Funny", "Bright", "Clever", "Silent", "Gentle", "Fierce", "Mighty", "Rapid", "Kind", "Calm", "Shiny", "Witty", "Bold", "Charming"]
    nouns = ["Tiger", "Eagle", "Panda", "Dolphin", "Fox", "Wolf", "Hawk", "Lion", "Shark", "Falcon", "Bear", "Cheetah", "Otter", "Rabbit", "Panther", "Leopard", "Penguin", "Seal"]
    random_number = random.randint(100, 999)  # Generate a random number for uniqueness
    
    fullname = f"{random.choice(adjectives)} {random.choice(nouns)}"
    username = f"{fullname.replace(' ', '')}{random_number}".lower()
    
    return username, fullname


def generate_random_password(length=12):
    """
    Generate a random password with a mix of uppercase, lowercase, digits, and symbols.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


async def generate_random_avatar(username):
    # Folder name to save avatars
    folder_name = "assets/avatars"

    # Check if folder exists; if not, create it
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    try:
        # Define the available avatar styles
        styles = [
            "adventurer",
            "adventurer-neutral",
            "avataaars",
            "avataaars-neutral",
            "big-ears",
            "big-ears-neutral",
            "big-smile",
            # "bottts",
            # "bottts-neutral",
            "croodles",
            "croodles-neutral",
            "dylan",
            "fun-emoji",
            # "glass",
            # "icons",
            # "identicon",
            # "initials",
            "lorelei",
            "lorelei-neutral",
            "micah",
            "miniavs",
            "notionists",
            "notionists-neutral",
            "open-peeps",
            "personas",
            # "pixel-art",
            # "pixel-art-neutral",
            # "rings",
            # "shapes",
            # "thumbs"
        ]

        # Randomly choose a style
        random_style = random.choice(styles)

        # Generate a random seed
        random_seed = f"{random.randint(1, 100000)}"  # Random seed value

        # Construct avatar URL based on selected style
        avatar_url = f"https://api.dicebear.com/9.x/{random_style}/png?seed={random_seed}&format=png"

        # Download the avatar
        print(f"Fetching avatar from: {avatar_url}")
        cl = httpx.AsyncClient()
        response = await cl.get(avatar_url)

        if response.status_code == 200:
            # File path to save the avatar
            file_path = os.path.join(folder_name, f"{username}_avatar_{random_style.replace('-', '_')}.png")

            # Save the avatar locally
            with open(file_path, "wb") as avatar_file:
                avatar_file.write(response.content)
            print(f"Avatar saved successfully: {file_path}")
            return file_path
        else:
            print(f"Failed to fetch avatar from: {avatar_url}")

    except Exception as e:
        print(f"Error occurred while fetching avatars: {e}")

    return None


def generate_random_bio():

    # List of predefined bio messages
    bio_list = [
        "Stock market enthusiast with a passion for data analysis and trends.",
        "Investor with a focus on tech stocks and growth opportunities.",
        "Crypto trader exploring the future of blockchain and digital assets.",
        "Financial analyst sharing insights and tips on stock market movements.",
        "Long-term investor with a focus on sustainable and ethical investing."
    ]

    # List of predefined areas of interest (specific to stocks, markets, etc.)
    interests_list = [
        "BURU ticker and its market potential",
        "Tech stocks and growth opportunities",
        "Cryptocurrency and blockchain technology",
        "Long-term sustainable investing",
        "Day trading and short-term market movements",
        "Index funds and passive investing",
        "Artificial Intelligence in finance",
        "Renewable energy stocks",
        "Real estate investment trusts (REITs)",
        "Emerging markets and international stocks",
        "Alternative investments like NFTs and digital assets"
    ]

    random_bio = random.choice(bio_list)
    random_interest = random.choice(interests_list)
    return f"{random_bio} Interested in: {random_interest}"


async def create_profiles():
    session = make_connection()
    gdb = GDBHelper(session)

    domains = [
        'accessoryjournal.org',
        'advanceddiagnosticsinsight.com',
        'advancedpackagingupdates.com',
        'adventureseekersunite.org',
        'advertisinginsightsnow.com',
        'advertisingtrendspotter.com',
        'aerialindustrynews.com',
        # 'aeroforcebase.com'
        'aeroimagazine.com',
        'aerospacedailynews.com',
    ]

    # Generate 10 random users per domain
    random_user_count = 10

    profiles = []

    for domain in domains:

        for _ in range(random_user_count):
            username, fullname = generate_random_user()
            password = generate_random_password()
            bio = generate_random_bio()
            avatar = await generate_random_avatar(username)
            
            profiles.append({
                'name': fullname,
                'email': f'{username}@{domain}',
                'password': password,
                'avatar': avatar,
                'bio': bio,
            })
    
    for profile in profiles:
        profile['profile_id'] = MakeTimedUniqueId()
        profile['user_id'] = 'admin'
        profile['start_page'] = 'https://www.google.com'
        profile['date_added'] = int(time.time())
        profile['date_updated'] = int(time.time())

    print(json.dumps(profiles, indent=4))

    await gdb.bulk_insert(Profile, profiles)
    
    await gdb.commit()
    
    await gdb.close()

    print('done')    
    

async def create_profiles_emails():
    session = make_connection()
    gdb = GDBHelper(session)

    # query = gdb.query(Profile)
    query = gdb.query(Profile).filter(Profile.created.is_(False))
    profiles = await gdb.all(query)
    
    for idx, profile in enumerate(profiles):
        print(f'{idx} / {len(profiles)}: {profile.name}')

        # create mailbox
        created = await create_mailbox(profile.toJSON())
        if created:
            profile.created = True
            profile.date_updated = int(time.time())
        
        await asyncio.sleep(0.3)  # Avoid rate limiting

    await gdb.commit()

    await gdb.close()

    print('done')    
    

async def create_profiles_stocktwits_accounts():
    session = make_connection()
    gdb = GDBHelper(session)

    query = gdb.query(Profile)
    profiles = await gdb.all(query)
    
    accounts = []
    
    for profile in profiles:
        print(profile.name)

        # create stocktwits account
        accounts.append({
            'account_id': MakeTimedUniqueId(),
            'profile_id': profile.profile_id,
            'website': 'https://stocktwits.com',
            'fullname': profile.name,
            'username': profile.email,
            'password': profile.password,
            'date_added': int(time.time()),
            'date_updated': int(time.time())
        })
        
    await gdb.bulk_insert(Account, accounts)

    await gdb.commit()

    await gdb.close()

    print('done')   


async def update_profiles_proxy_address():

    # read proxy file
    proxy_list = []
    with open('proxy.txt', 'r') as file:
        proxy_list = [line.strip() for line in file]
    
    # print(proxy_list)

    session = make_connection()
    gdb = GDBHelper(session)

    query = gdb.query(Profile)
    profiles = await gdb.all(query)

    updated_profiles = []
    for idx, profile in enumerate(profiles):
        
        print(f'{idx} / {len(proxy_list)}: {profile.name}')

        if idx > len(proxy_list) - 1:
            break
        
        proxy_type = 'http' # or SOCKS5
        proxy_addr = proxy_list[idx]
        
        
        updated_profiles.append({
            'profile_id': profile.profile_id,
            'proxy_type': proxy_type,
            'proxy_address': f'{proxy_addr}',
        })

    await gdb.bulk_update(Profile, updated_profiles)

    await gdb.commit()
    
    await gdb.close()

    
async def fetch_mailboxes():

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': os.getenv('MAILCOW_API_KEY')
    }
    
    client = httpx.AsyncClient()

    fetch_url = 'https://mail.aeroforcebase.com/api/v1/get/mailbox/all'
    resp = await client.get(fetch_url, headers=headers)
    data = resp.json()

    print(json.dumps(data[0], indent=4))


async def create_mailbox(profile):

    fullname = profile['name']
    email = profile['email']
    password = profile['password']
    username = email.split('@')[0]
    domain = email.split('@')[1]

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': os.getenv('MAILCOW_API_KEY')
    }
    
    payload = {
        "local_part": username,
        "domain": domain,
        "name": fullname,
        "quota": "1024",
        "password": password,
        "password2": password,
        "active": "1",
        "force_pw_update": "0",
        "tls_enforce_in": "1",
        "tls_enforce_out": "1",
    }
    
    client = httpx.AsyncClient()

    try:
    
        api_url = 'https://mail.aeroforcebase.com/api/v1/add/mailbox'
        resp = await client.post(api_url, data=json.dumps(payload), headers=headers, timeout=120)
        data = resp.json()
        
        # print(json.dumps(data, indent=4))

        if isinstance(data, dict) and data.get('type') == 'error':
            print(f'Error creating mailbox for {email}: {data.get("msg")}')
            return False
        
        if isinstance(data, list) and (len(data) > 0) and data[0]['type'] == 'danger':
            print(f'Error creating mailbox for {email}: {data[0].get("msg")}')
            return False

    except Exception as e:
        print(f'Error creating mailbox for {email}: {e}')
        return False

    return True


async def read_emails():

    box = EmailBox(
        host="mail.aeroforcebase.com", port=993,
        username='shinyseal167@aeroforcebase.com', password="""'`>p)ec]DXq^"""
    )

    inbox = box['INBOX']

    # for msg in inbox.search(UNSEEN & SUBJECT("Stocktwits")):
    for msg in inbox.search(SUBJECT("Stocktwits")):

        print(msg.subject)
        print(msg.from_)
        # print(msg.html_body)
        
        html_body = msg.html_body.replace('=\r\n', '').replace('=3D', '=')
            
        soup = BeautifulSoup(html_body, "html.parser")
        a_tags = soup.find_all('a')

        verify_url = None

        for a_tag in a_tags:
            if a_tag.text == 'Verify Your Email':
                verify_url = a_tag.get('href').strip('"')
                print(a_tag.text)
                print(verify_url)
                break
        

async def update_status_in_db(account_id, event):
    print(f'update_status account_id: {account_id} event: {event}')
    
    session = make_connection()
    gdb = GDBHelper(session)
    
    account: Account = await gdb.get(Account, account_id)
    profile: Profile = await gdb.get(Profile, account.profile_id)

    if event == 'account_created':
        account.created = True
        account.date_updated = int(time.time())

    elif event == 'account_verified':
        account.verified = True
        account.date_updated = int(time.time())

    elif event == 'account_blocked':
        account.blocked = True
        account.date_updated = int(time.time())

    elif event == 'activity_started':
        profile.status = 'Active'
        profile.last_used = int(time.time())

    elif event == 'activity_stopped':
        profile.status = 'Inactive'
        profile.last_used = int(time.time())

    await gdb.commit()

    await gdb.close()


async def create_stocktwits_accounts():

    while True:
        session = make_connection()
        gdb = GDBHelper(session)

        query = gdb.query(Account).filter(Account.created.is_(False)).limit(1)
        account = await gdb.one_or_none(query)
                
        if account is None:
            print('===> no accounts to signup')

        if account is not None:

            print('try to signup account: ', account.fullname)
            
            profile: Profile = await gdb.get(Profile, account.profile_id)

            # create stocktwits account
            app = Stocktwits(
                account.account_id, 'Stocktwits', 
                proxy_type=profile.proxy_type, proxy_address=profile.proxy_address,
                username=account.username, password=account.password, fullname=account.fullname, 
                update_status_in_db=update_status_in_db)

            await gdb.close()

            await app.signup()
        
        await asyncio.sleep(180)  # Avoid blockoing

                
async def verify_stocktwits_accounts():

    while True:
        session = make_connection()
        gdb = GDBHelper(session)

        query = gdb.query(Account).filter(
            Account.created.is_(True),
            Account.verified.is_(False)).limit(1)
        account = await gdb.one_or_none(query)
        
        if account is None:
            print('===> no accounts to verify')

        if account is not None:
                
            print('verify account ', account.fullname)
            
            profile: Profile = await gdb.get(Profile, account.profile_id)

            # create stocktwits account
            app = Stocktwits(
                account.account_id, 'Stocktwits', 
                proxy_type=profile.proxy_type, proxy_address=profile.proxy_address,
                username=account.username, password=account.password, fullname=account.fullname, 
                avatar=profile.avatar, bio=profile.bio,
                update_status_in_db=update_status_in_db)

            await gdb.close()

            await app.verify()
        
        await asyncio.sleep(30)
       

async def test_stocktwits_activity():

    session = make_connection()
    gdb = GDBHelper(session)

    query = gdb.query(Account).filter(
        Account.created.is_(True),
        Account.verified.is_(True),
        Profile.status == 'Inactive'
    ).join(
        Profile, Account.profile_id == Profile.profile_id
    ).limit(1)
    account = await gdb.one_or_none(query)

    if account is None:
        print('===> no accounts to start activity')

    if account is not None:
            
        print('start account activity', account.fullname)
        
        profile: Profile = await gdb.get(Profile, account.profile_id)

        # create stocktwits account
        app = Stocktwits(
            account.account_id, 'Stocktwits', 
            proxy_type=profile.proxy_type, proxy_address=profile.proxy_address,
            username=account.username, password=account.password, fullname=account.fullname, 
            avatar=profile.avatar, bio=profile.bio)

        await gdb.close()

        await app.start_activity()


async def start_stocktwits_activity(start=0, limit=10):

    session = make_connection()
    gdb = GDBHelper(session)

    query = gdb.query(Account).filter(
        Account.created.is_(True),
        Account.verified.is_(True)
    ).limit(limit).offset(start)
    accounts = await gdb.all(query)

    continues = []

    for account in accounts:
        profile: Profile = await gdb.get(Profile, account.profile_id)

        print('account', account.fullname)

        app = Stocktwits(
            account.account_id, 'Stocktwits', 
            proxy_type=profile.proxy_type, proxy_address=profile.proxy_address,
            username=account.username, password=account.password, fullname=account.fullname, 
            avatar=profile.avatar, bio=profile.bio)

        continues.append(app.start())
    
    await gdb.close()
    
    await asyncio.sleep(3)

    await asyncio.gather(
        *continues
    )

       
async def check_mailcow_domain_setup(domain):

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': os.getenv('MAILCOW_API_KEY')
    }
    
    client = httpx.AsyncClient()

    try:
    
        api_url = f'https://mail.aeroforcebase.com/api/v1/get/domain/{domain}'
        resp = await client.get(api_url, headers=headers)
        data = resp.json()
        # print(json.dumps(data, indent=4))

        if len(data) > 0:
            return True

    except Exception as e:
        print(f'Error checking mailcow domain for {domain}: {e}')
        raise e
    
    return False


async def setup_mailcow_domain(domain):

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': os.getenv('MAILCOW_API_KEY')
    }
    
    payload = {
        "domain": domain,
        "description": "",
        "aliases": "100",
        "mailboxes": "100",
        "defquota": "1024",
        "maxquota": "2048",
        "quota": "102400",
        "active": "1",
        "rl_value": "",
        "rl_frame": "s",
        "backupmx": "0",
        "relay_all_recipients": "0",
        "restart_sogo": "1"
    }
    
    client = httpx.AsyncClient()

    try:
    
        api_url = 'https://mail.aeroforcebase.com/api/v1/add/domain'
        resp = await client.post(api_url, data=json.dumps(payload), headers=headers, timeout=120)
        data = resp.json()

        # print(json.dumps(data, indent=4))
        
        if isinstance(data, dict) and data.get('type') == 'error':
            print(f'Error creating mailbox for {domain}: {data.get("msg")}')
            return False
        
        if isinstance(data, list) and (len(data) > 0) and data[0]['type'] == 'danger':
            print(f'Error creating mailbox for {domain}: {data[0].get("msg")}')
            return False
        
    except Exception as e:
        traceback.print_exc()
        print(f'Error creating domain for {domain}: {e}')
        return False

    return True
       

async def fetch_dmarc_key(domain):

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': os.getenv('MAILCOW_API_KEY')
    }
    
    client = httpx.AsyncClient()

    try:
    
        api_url = f'https://mail.aeroforcebase.com/api/v1/get/dkim/{domain}'
        resp = await client.get(api_url, headers=headers)
        data = resp.json()
        # print(json.dumps(data, indent=4))
        
        if len(data) > 0:
            dkim_key = data.get('dkim_txt')
            return dkim_key

    except Exception as e:
        print(f'Error fetching mailcow dkim for {domain}: {e}')
        raise e
    
    return None
             
async def configure_domain_email(domain):

    print(f'Configuring domain: {domain}')

    # check if not already setup
    already_setup = await check_mailcow_domain_setup(domain)

    if already_setup:
        print(f'Domain {domain} is already setup')
        print('Exiting...')
        return
        
    # # mailcow setup
    domain_setup = await setup_mailcow_domain(domain)
    if not domain_setup:
        print(f'Error while setting up domain {domain}')
        print('Exiting...')
        return

    print(f'Domain {domain} setup successfully')

    support_email = f'support@{domain}'
    print(f'creating mailbox: {support_email}')

    mailbox_created = await create_mailbox({'name': f'Support <{support_email}>', 'email': support_email, 'password': 'Admin@123!@#'})
    if not mailbox_created:
        print(f'Error while creating mailbox: {support_email}')

    print(f'fetching dkim for {domain}')
    dmarc_key = await fetch_dmarc_key(domain)
    if not dmarc_key:
        print(f'Error while fetching dkim for {domain}')
        return
        
    # name cheap api
    username = 'chaudhry9077'
    api_key = os.getenv('NAMECHEAP_API_KEY')
    whitelist_ip = '154.192.136.21'

    email_server_ip = '66.94.103.160'

    host_records = [{
        "RecordType": "A",
        "HostName": "mail",
        "Address": email_server_ip,
        "MXPref": 10,
        "TTL": 1800
    }, {
        "RecordType": "TXT",
        "HostName": "@",
        "Address": f"v=spf1 ip4:{email_server_ip} ~all",
        "MXPref": 10,
        "TTL": 1800
    }, {
        "RecordType": "TXT",
        "HostName": "dmarc",
        "Address": dmarc_key,
        "MXPref": 10,
        "TTL": 1800
    }]
    
    api = NamecheapApi(username, api_key, username, whitelist_ip, sandbox=False)
    print('Adding host records for', domain)
    for idx, host_record in enumerate(host_records):
        print(f'record: {idx+1} / {len(host_records)}')
        api.domains_dns_addHost(domain, host_record)
        time.sleep(1)

    print('done')


async def setup_domains():
    domains_list = []
    with open('domains.json', 'r') as file:
        domains_list = json.load(file)
    
    for idx, domain_item in enumerate(domains_list[0:10]):
        domain = domain_item['Name']
        print(f'{idx} / {len(domains_list)}: {domain}')
        # await configure_domain_email(domain)
        await asyncio.sleep(0.3)

    print('domains setup successfully')


async def fetch_namecheap_domains():
    
    username = 'chaudhry9077'
    api_key = os.getenv('NAMECHEAP_API_KEY')
    whitelist_ip = '154.192.136.21'
    
    domain_list = []
    
    api = NamecheapApi(username, api_key, username, whitelist_ip, sandbox=False)
    domains = api.domains_getList()
    for domain in domains:
        print(domain)
        time.sleep(0.2)
        domain_list.append(domain)

    with open('domains.json', 'w') as f:
        json.dump(domain_list, f)
    
    print('done') 


async def fetch_domain_hosts(domain):
    
    username = 'chaudhry9077'
    api_key = os.getenv('NAMECHEAP_API_KEY')
    whitelist_ip = '154.192.136.21'
    
    api = NamecheapApi(username, api_key, username, whitelist_ip, sandbox=False)
    # domains = api.domains_getList()
    # for domain in domains:
    #     print(domain)
    
    print('--------')
    resp = api.domains_dns_getHosts(domain)
    print(resp)
    
    print('done')    
       

async def update_mailtype_mx(domain):

    cookies = {
        'x-auth-deviceverification': '296b2001-c1ff-499b-94b4-977487883e6f',
        '.c': 'USD',
        '_gcl_gs': '2.1.k1$i1731088903$u78916747',
        '_gcl_au': '1.1.1724342096.1731088905',
        '_gcl_aw': 'GCL.1731088908.Cj0KCQiAire5BhCNARIsAM53K1iwvRjpv9FC4s8V_nwuI_NiUtl_ywuHwBkbLart-uH2H6qdMVn4be0aAjPKEALw_wcB',
        '_ga': 'GA1.1.2127048742.1731088908',
        'SessionId': '0d8322d9c3f74b3687823082a4b976ee',
        '.s': 'aadad03f1ef048ebb38949d32f31d945',
        'BIGipServerap.www.namecheap.com_http-rev1': '230888458.20480.0000',
        'carttotalnoofitemscookie': '%7B%22ItemCount%22%3A0%2C%22CartTotal%22%3A0%2C%22FormattedCartTotal%22%3A%22%240.00%22%7D',
        'IR_gbd': 'namecheap.com',
        'cebs': '1',
        'x-ncpl-csrf': '04fee4c15b704352bd50813921819fad',
        '_NcCompliance': 'd5f2c07c-c44a-4753-9d24-d9a96bd45fbd',
        'x-gdpr-sessionid': 'g464963260.1733912267',
        '_CMSNavigation': 'fyj30/D9nQFff4ao6LXK9zROaJRu1z97+eDqcmh+8Xh1g5Vyi5zGng==',
        '__cflb': '02DiuEFj9FbkmbhdBGRXg4V9w49XAYiK5ftazQ841C7nc',
        '_ce.clock_data': '-4%2C154.192.46.85%2C1%2C24e87e5f156ab48c5bb559e4c1652234%2CChrome%2CPK',
        '_cfuvid': 'He3WiL3ZKQ4ucdTG5rpDp2TBdZQSqH8J78YWmqW9dUI-1735799271459-0.0.1.1-604800000',
        'x-sf-country': '63d1c2e009cfeb5ac8e1e9fe1af92dfcb36a1c56b468f031d1e4717aec0660c5|--',
        'U': '57c88f70775ee383892d0950cda7afc8',
        'x-auth-recall': 'ADzOyVmEx8LaxCAci0E19+8XogbKJd3IN4TPZ61Rvn4mb2KewTyEkjydrUX7eNrf/xVwDzY+zTJnhmhRHZxrD0RsAyz57VigFb4lLZWXrtCK6fZ5Sdc4Y1ODBQY2fM9ETHcnOer3aJGYUtlE53FFEXYpeQYg6qELVMXxPY6YGIdpcwCb7TShQ5R+jtPefAh9Lc/LZFp8t2tGaBnWjnmpWmqWnUhTD2ue7cCqBomcwBTyayL3izs8hbNabmExqbcN+dZmhPARlP+dNpryK3nOwgN3vX/Ldes1jxjct5x7Ey41NBrF6QRl4+WZdXzAtlnaHnwg4FVK7T7mm/wA8PYP78gUa4la9BIaUjCrzV/ZwzR9NHuj3ViZa30O0KbrB9yLUjqP2AnSC+e/6XBXIWdI5ik5BC4mn1G/5zrSN0/8ndogKGJ0',
        '.ncauth': 'C53B5751B6675002EA05DC50AF4B244C4C0F1325D04BE251BB75459D73BF65D473A7E5DC3195B115DAA915AE67F0577C7BC8756E0A7F8EF848F368F738129F16FDCEAE96CBF8E9955769B13FE01A9D8344C4C739467C0C40CD24213CDBBD0859062C98FB69441E2C9FEAD8A948BDAF25D2F760E729F32D15D928A8066892B5F099B9D59988E8C495FC3AF90ED7C4B4FAA423646B5CE23ECF0AC31005BEA876DCBD7DE4B9FD949CCB2F5690E57B7168B6D75A56465CE63FB3514240EE1F511F392E7F16CDAC2A0019712F334F5C2345119D28CD2ADF6D8C8C8E4071936AD58AF37B25BD7217E45C5B70D31468D82A2E9131950A1E7D31B00F4A57098E9824DB95EAFFB88433FA462266309EB69EEE3C737231821B2A56FCCD5F435B55DA5C20AEB7145C34A5925B7AE03212FE9323DAA60BBFD0CE2CB8B247EB9BDE937FA5D01E1A844889F570608CFE4739AB40D1C8A243416DA90BFF5E6DB570B34CFB18E6EBFB52375FD4830E75493D73C6ABD179A8139B4C388EC9AC65E67EDAD14C02454C3AEBE7B0D00A2E9B019E67EF39246577C940F156E4F2864657999761FE117D57A645BE81B4758C7F1EFF23DBEFFA4C536532755D025772A575BB38C7ADD949690B238F46F04EA0B0B0BA817D3B2B28953126110F0B68B0E04E062AB1A61E26048467EC9DD6820C458E968C264793670652FB3FD5637B1973C43556D579860F24297DD630B6187620147AD43D2C545C98F6FF3194CA0DAAF5005599C9775DDD148D7878201D26DA36852A3B0F2C08BE6D3D55E65B2C3DCBA778F1A0FC741B218BA1FFF6EE',
        'x-ncpl-auth': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjaGF1ZGhyeTkwNzciLCJuYy9ncnMiOiJuY1VzZXIiLCJuYy9ybHMiOiJuY1VzZXI7ZXh0IiwibmMvY2xpIjoiY2hhdWRocnk5MDc3IiwibmMvdWlkIjoiMTQzNjg4OTUiLCJuYy9zaWQiOiIxNDM2ODg5NS1mZTdiZWQxMmZiMjE0YTJmOTYzMzU5MzhiOGNmZmY0NSIsIm5jL3NsZCI6IjEiLCJuYy9kb20iOiIud3d3Lm5hbWVjaGVhcC5jb20iLCJuYy9mY3NyZiI6IjEiLCJuYy92YyI6IjE0MzY4ODk1LTZlOGNjMDhlYmMzZDQwODM4ZWNlODQ3MjMzZTI5YjhiIiwibmJmIjoxNzM1ODEwOTUzLCJleHAiOjE3MzU4MTgxNDksImlhdCI6MTczNTgxMDk1MywiaXNzIjoiaHR0cDovL25hbWVjaGVhcC5jb20iLCJhdWQiOiIqIn0.9hPfaDFBLMDqR1kusAp7tX9533QQKYehBCcf6nmtZ8c',
        '__ControllerTempData': 'VpemDMPyWQxX+zxAqZ80qRwkPiCkXI8EgtCwlBJDlggb7Kh7cYltxOm9pcAwgsH1knxDYPF03Qu6+9yMWdlohZ1gSQLxp78aDCLLSy4C6iIW0Jj1OCpy2WVVbHooXQvOZg0Ne+V7Ub9ZRIhcfB+yx1PQ7wsVPACFlhIW+y1vZ6jANmtAa21PK5oQGAwjRRao9mKkBIJCZhR78kh7YweLKz03jpbfjdFCFFQ9Awsa1p0HVIMDThwEfsMYjZL9Y9GyTYyw0sbYiqx/OGMj6Zev4ca4GZZjKdu+dXFNAeA8qVoqTbbujepLGWUsPQB4ETifMM1dYDkMqSMtdHpCbdUQX2f6jY4v+yV8GwMZmlFC9/L1w5M89Gk+0+WDOaD2w4pvQTrpxrjwLJ/zxK9y8apF1OHmZBdwMY3o9JyoElnVaQc6KEZl+2nwzbNnakrQcSZDf9IesZHsQWRoKtFrBHl4JkKNQ+BtDaMqtalV06a1ZPStqtxNY8K86BJr+w3Ll3O/MHZaDGZn8bKyFJnM4bgvNLXAWpgfFWLJNBQpTO52S0PdwxNhmbo7UwZH1wMPH6HJYuckN6fYY5HtvN0oARG3Pog9W7QM2Fub5EaFSVk9Xp+UMcfDMXraHmEdDBi39/GTUTTOx2VgYh5GO2Aiz403GA==',
        'IR_5618': '1735811110638%7C0%7C1735811110638%7C%7C',
        'cebsp_': '106',
        'IR_PI': '5918342d-5845-11ee-bacb-1dab2dc0e8e7%7C1735811110638',
        '_ga_7DMJMG20P8': 'GS1.1.1735799272.16.1.1735811111.41.0.0',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+Jan+02+2025+14%3A45%3A11+GMT%2B0500+(Pakistan+Standard+Time)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false&geolocation=PK%3BIS',
        'OptanonAlertBoxClosed': '2025-01-02T09:45:11.320Z',
        '_uetsid': '9a6da960c84b11ef97c30d9160c7eefa',
        '_uetvid': '1cc0e8709f2111eeb5f429b778480322',
        '_ce.s': 'v~da849cba9463a6887870a8c3a1d48a6a8273f91d~lcw~1735811416395~vir~returning~lva~1735741250906~vpv~2~v11.fhb~1735558256618~v11.lhb~1735811403219~v11.cs~205054~v11.s~763e38f0-c8e5-11ef-81fb-5d2e2e5eef07~v11.sla~1735811416801~lcw~1735811416802',
    }

    headers = {
        'authority': 'ap.www.namecheap.com',
        '_nccompliance': 'd5f2c07c-c44a-4753-9d24-d9a96bd45fbd',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json;charset=UTF-8',
        # 'cookie': 'x-auth-deviceverification=296b2001-c1ff-499b-94b4-977487883e6f; .c=USD; _gcl_gs=2.1.k1$i1731088903$u78916747; _gcl_au=1.1.1724342096.1731088905; _gcl_aw=GCL.1731088908.Cj0KCQiAire5BhCNARIsAM53K1iwvRjpv9FC4s8V_nwuI_NiUtl_ywuHwBkbLart-uH2H6qdMVn4be0aAjPKEALw_wcB; _ga=GA1.1.2127048742.1731088908; SessionId=0d8322d9c3f74b3687823082a4b976ee; .s=aadad03f1ef048ebb38949d32f31d945; BIGipServerap.www.namecheap.com_http-rev1=230888458.20480.0000; carttotalnoofitemscookie=%7B%22ItemCount%22%3A0%2C%22CartTotal%22%3A0%2C%22FormattedCartTotal%22%3A%22%240.00%22%7D; IR_gbd=namecheap.com; cebs=1; x-ncpl-csrf=04fee4c15b704352bd50813921819fad; _NcCompliance=d5f2c07c-c44a-4753-9d24-d9a96bd45fbd; x-gdpr-sessionid=g464963260.1733912267; _CMSNavigation=fyj30/D9nQFff4ao6LXK9zROaJRu1z97+eDqcmh+8Xh1g5Vyi5zGng==; __cflb=02DiuEFj9FbkmbhdBGRXg4V9w49XAYiK5ftazQ841C7nc; _ce.clock_data=-4%2C154.192.46.85%2C1%2C24e87e5f156ab48c5bb559e4c1652234%2CChrome%2CPK; _cfuvid=He3WiL3ZKQ4ucdTG5rpDp2TBdZQSqH8J78YWmqW9dUI-1735799271459-0.0.1.1-604800000; x-sf-country=63d1c2e009cfeb5ac8e1e9fe1af92dfcb36a1c56b468f031d1e4717aec0660c5|--; U=57c88f70775ee383892d0950cda7afc8; x-auth-recall=ADzOyVmEx8LaxCAci0E19+8XogbKJd3IN4TPZ61Rvn4mb2KewTyEkjydrUX7eNrf/xVwDzY+zTJnhmhRHZxrD0RsAyz57VigFb4lLZWXrtCK6fZ5Sdc4Y1ODBQY2fM9ETHcnOer3aJGYUtlE53FFEXYpeQYg6qELVMXxPY6YGIdpcwCb7TShQ5R+jtPefAh9Lc/LZFp8t2tGaBnWjnmpWmqWnUhTD2ue7cCqBomcwBTyayL3izs8hbNabmExqbcN+dZmhPARlP+dNpryK3nOwgN3vX/Ldes1jxjct5x7Ey41NBrF6QRl4+WZdXzAtlnaHnwg4FVK7T7mm/wA8PYP78gUa4la9BIaUjCrzV/ZwzR9NHuj3ViZa30O0KbrB9yLUjqP2AnSC+e/6XBXIWdI5ik5BC4mn1G/5zrSN0/8ndogKGJ0; .ncauth=C53B5751B6675002EA05DC50AF4B244C4C0F1325D04BE251BB75459D73BF65D473A7E5DC3195B115DAA915AE67F0577C7BC8756E0A7F8EF848F368F738129F16FDCEAE96CBF8E9955769B13FE01A9D8344C4C739467C0C40CD24213CDBBD0859062C98FB69441E2C9FEAD8A948BDAF25D2F760E729F32D15D928A8066892B5F099B9D59988E8C495FC3AF90ED7C4B4FAA423646B5CE23ECF0AC31005BEA876DCBD7DE4B9FD949CCB2F5690E57B7168B6D75A56465CE63FB3514240EE1F511F392E7F16CDAC2A0019712F334F5C2345119D28CD2ADF6D8C8C8E4071936AD58AF37B25BD7217E45C5B70D31468D82A2E9131950A1E7D31B00F4A57098E9824DB95EAFFB88433FA462266309EB69EEE3C737231821B2A56FCCD5F435B55DA5C20AEB7145C34A5925B7AE03212FE9323DAA60BBFD0CE2CB8B247EB9BDE937FA5D01E1A844889F570608CFE4739AB40D1C8A243416DA90BFF5E6DB570B34CFB18E6EBFB52375FD4830E75493D73C6ABD179A8139B4C388EC9AC65E67EDAD14C02454C3AEBE7B0D00A2E9B019E67EF39246577C940F156E4F2864657999761FE117D57A645BE81B4758C7F1EFF23DBEFFA4C536532755D025772A575BB38C7ADD949690B238F46F04EA0B0B0BA817D3B2B28953126110F0B68B0E04E062AB1A61E26048467EC9DD6820C458E968C264793670652FB3FD5637B1973C43556D579860F24297DD630B6187620147AD43D2C545C98F6FF3194CA0DAAF5005599C9775DDD148D7878201D26DA36852A3B0F2C08BE6D3D55E65B2C3DCBA778F1A0FC741B218BA1FFF6EE; x-ncpl-auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjaGF1ZGhyeTkwNzciLCJuYy9ncnMiOiJuY1VzZXIiLCJuYy9ybHMiOiJuY1VzZXI7ZXh0IiwibmMvY2xpIjoiY2hhdWRocnk5MDc3IiwibmMvdWlkIjoiMTQzNjg4OTUiLCJuYy9zaWQiOiIxNDM2ODg5NS1mZTdiZWQxMmZiMjE0YTJmOTYzMzU5MzhiOGNmZmY0NSIsIm5jL3NsZCI6IjEiLCJuYy9kb20iOiIud3d3Lm5hbWVjaGVhcC5jb20iLCJuYy9mY3NyZiI6IjEiLCJuYy92YyI6IjE0MzY4ODk1LTZlOGNjMDhlYmMzZDQwODM4ZWNlODQ3MjMzZTI5YjhiIiwibmJmIjoxNzM1ODEwOTUzLCJleHAiOjE3MzU4MTgxNDksImlhdCI6MTczNTgxMDk1MywiaXNzIjoiaHR0cDovL25hbWVjaGVhcC5jb20iLCJhdWQiOiIqIn0.9hPfaDFBLMDqR1kusAp7tX9533QQKYehBCcf6nmtZ8c; __ControllerTempData=VpemDMPyWQxX+zxAqZ80qRwkPiCkXI8EgtCwlBJDlggb7Kh7cYltxOm9pcAwgsH1knxDYPF03Qu6+9yMWdlohZ1gSQLxp78aDCLLSy4C6iIW0Jj1OCpy2WVVbHooXQvOZg0Ne+V7Ub9ZRIhcfB+yx1PQ7wsVPACFlhIW+y1vZ6jANmtAa21PK5oQGAwjRRao9mKkBIJCZhR78kh7YweLKz03jpbfjdFCFFQ9Awsa1p0HVIMDThwEfsMYjZL9Y9GyTYyw0sbYiqx/OGMj6Zev4ca4GZZjKdu+dXFNAeA8qVoqTbbujepLGWUsPQB4ETifMM1dYDkMqSMtdHpCbdUQX2f6jY4v+yV8GwMZmlFC9/L1w5M89Gk+0+WDOaD2w4pvQTrpxrjwLJ/zxK9y8apF1OHmZBdwMY3o9JyoElnVaQc6KEZl+2nwzbNnakrQcSZDf9IesZHsQWRoKtFrBHl4JkKNQ+BtDaMqtalV06a1ZPStqtxNY8K86BJr+w3Ll3O/MHZaDGZn8bKyFJnM4bgvNLXAWpgfFWLJNBQpTO52S0PdwxNhmbo7UwZH1wMPH6HJYuckN6fYY5HtvN0oARG3Pog9W7QM2Fub5EaFSVk9Xp+UMcfDMXraHmEdDBi39/GTUTTOx2VgYh5GO2Aiz403GA==; IR_5618=1735811110638%7C0%7C1735811110638%7C%7C; cebsp_=106; IR_PI=5918342d-5845-11ee-bacb-1dab2dc0e8e7%7C1735811110638; _ga_7DMJMG20P8=GS1.1.1735799272.16.1.1735811111.41.0.0; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Jan+02+2025+14%3A45%3A11+GMT%2B0500+(Pakistan+Standard+Time)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false&geolocation=PK%3BIS; OptanonAlertBoxClosed=2025-01-02T09:45:11.320Z; _uetsid=9a6da960c84b11ef97c30d9160c7eefa; _uetvid=1cc0e8709f2111eeb5f429b778480322; _ce.s=v~da849cba9463a6887870a8c3a1d48a6a8273f91d~lcw~1735811416395~vir~returning~lva~1735741250906~vpv~2~v11.fhb~1735558256618~v11.lhb~1735811403219~v11.cs~205054~v11.s~763e38f0-c8e5-11ef-81fb-5d2e2e5eef07~v11.sla~1735811416801~lcw~1735811416802',
        'origin': 'https://ap.www.namecheap.com',
        'pragma': 'no-cache',
        'referer': f'https://ap.www.namecheap.com/Domains/DomainControlPanel/{domain}/advancedns',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

    json_data = {
        'domainName': domain,
        'emailType': 2,
        'hostRecordList': [
            {
                'Host': '@',
                'Data': f'mail.{domain}',
                'Priority': '0',
                'RecordType': 3,
                'Ttl': 1799,
            },
        ],
    }

    response = requests.post(
        'https://ap.www.namecheap.com/Domains/Dns/UpdateEmailType',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )   
    
    print(response)
    print('done')
       

async def update_mailtype():
    domains_list = []
    with open('domains.json', 'r') as file:
        domains_list = json.load(file)
    
    for idx, domain_item in enumerate(domains_list[10:]):
        domain = domain_item['Name']
        print(f'{idx} / {len(domains_list)}: {domain}')
        await update_mailtype_mx(domain)
        time.sleep(0.3)


async def test_verify():

    session = make_connection()
    gdb = GDBHelper(session)

    query = gdb.query(Account).filter(
        Account.created.is_(True),
        Account.verified.is_(True)).limit(1)
    account = await gdb.one_or_none(query)
    
    if account is None:
        print('===> no accounts to verify')

    if account is not None:
            
        print('verify account ', account.fullname)
        
        profile: Profile = await gdb.get(Profile, account.profile_id)

        # create stocktwits account
        app = Stocktwits(
            account.account_id, 'Stocktwits', 
            proxy_type=profile.proxy_type, proxy_address=profile.proxy_address,
            username=account.username, password=account.password, fullname=account.fullname, 
            avatar=profile.avatar, bio=profile.bio)

        await gdb.close()

        await app.verify()

async def main():

    await asyncio.gather(*[
        create_stocktwits_accounts(),
        verify_stocktwits_accounts()        
    ])


if __name__ == "__main__":
    load_dotenv(override=True)

    # asyncio.run(setup_domains())
    
    # asyncio.run(create_profiles())
    
    # asyncio.run(create_profiles_emails())

    # asyncio.run(create_profiles_stocktwits_accounts())
    
    # asyncio.run(update_profiles_proxy_address())

    # asyncio.run(fetch_mailboxes())

    # domain = 'aeroforcebase.com'
    # asyncio.run(fetch_domain_hosts(domain))

    # asyncio.run(fetch_namecheap_domains())

    # asyncio.run(update_mailtype())
    
    # asyncio.run(test_verify())

    start = int(os.getenv('ACCOUNT_START', '0'))
    limit = int(os.getenv('ACCOUNT_LIMIT', '1'))

    asyncio.run(test_stocktwits_activity())
    
    # asyncio.run(main())

    print('---done---')
