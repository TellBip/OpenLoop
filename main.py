from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
from core.config import (
    CAPTCHA_SERVICE, 
    CAPTCHA_API_KEY, 
    MAX_AUTH_THREADS, 
    MAX_REG_THREADS, 
    INVITE_CODE, 
    CAPTCHA_WEBSITE_KEY, 
    CAPTCHA_WEBSITE_URL,
    MAX_RETRIES
)
from core.captcha import ServiceCapmonster, ServiceAnticaptcha, Service2Captcha, CFLSolver
from httpx import AsyncClient
import asyncio, random, json, os, pytz
from itertools import islice
from solders.keypair import Keypair
from solders.message import Message
from solders.transaction import Transaction
from base64 import b64encode

# Setting time zone
wib = pytz.timezone('Asia/Jakarta')

# Colorama initialization for Windows
init(autoreset=True)

class OpenLoop:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "chrome-extension://effapmdildnpkiaeghlkicpfflpiambm",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.session = None
        
        # Captcha service initialization
        if CAPTCHA_SERVICE.lower() == "2captcha":
            self.captcha_solver = Service2Captcha(CAPTCHA_API_KEY)
        elif CAPTCHA_SERVICE.lower() == "capmonster":
            self.captcha_solver = ServiceCapmonster(CAPTCHA_API_KEY)
        elif CAPTCHA_SERVICE.lower() == "anticaptcha":
            self.captcha_solver = ServiceAnticaptcha(CAPTCHA_API_KEY)
        elif CAPTCHA_SERVICE.lower() == "cflsolver":
            self.http_client = AsyncClient()
            self.captcha_solver = CFLSolver(CAPTCHA_API_KEY, self.http_client)
        else:
            raise ValueError(f"Unsupported captcha service: {CAPTCHA_SERVICE}")

    async def start(self):
        """Session initialization"""
        if self.session is None:
            self.session = ClientSession()
        return self

    async def stop(self):
        """Session closure"""
        if self.session:
            await self.session.close()
            self.session = None
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        telegram_link = "https://t.me/+1fc0or8gCHsyNGFi"
        print(f"""
        {Fore.GREEN + Style.BRIGHT}
         OOO  PPPP  EEEE N   N L     OOO   OOO  PPPP
        O   O P   P E    NN  N L    O   O O   O P   P
        O   O PPPP  EEE  N N N L    O   O O   O PPPP
        O   O P     E    N  NN L    O   O O   O P
         OOO  P     EEEE N   N LLLL  OOO   OOO  P
        {Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}Developed by: @Tell_Bip{Style.RESET_ALL}
{Fore.GREEN + Style.BRIGHT}Our Telegram channel:{Style.RESET_ALL} {Fore.BLUE + Style.BRIGHT}\x1b]8;;{telegram_link}\x07{telegram_link}\x1b]8;;\x07{Style.RESET_ALL}
        """)

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self, operation_type: str = None):
        """Loads accounts based on operation type (reg/auth/farm/connect_wallet)"""
        filename = {
            "reg": "data/reg.txt",
            "auth": "data/auth.txt",
            "farm": "data/farm.txt",
            "connect_wallet": "data/wallet.txt"
        }.get(operation_type, "accounts.txt")

        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File '{filename}' not found.{Style.RESET_ALL}")
                return []
            accounts = []
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if operation_type == "connect_wallet":
                        if ':' in line:
                            parts = line.split(':', 2)
                            if len(parts) == 3:
                                email, password, private_key = parts
                                accounts.append({
                                    "Email": email.strip(), 
                                    "Password": password.strip(), 
                                    "PrivateKey": private_key.strip()
                                })
                    elif line and ':' in line:
                        email, password = line.split(':', 1)
                        accounts.append({"Email": email.strip(), "Password": password.strip()})
            return accounts
        except Exception as e:
            self.log(f"{Fore.RED}Error loading accounts: {e}{Style.RESET_ALL}")
            return []
    
    def save_results(self, operation_type: str, success_accounts: list, failed_accounts: list):
        """Saves operation results to appropriate files"""
        try:
            if not os.path.exists('result'):
                os.makedirs('result')

            # Define filenames based on operation type
            success_file = {
                "reg": "result/good_reg.txt",
                "auth": "result/good_auth.txt",
                "farm": "result/good_farm.txt",
                "connect_wallet": "result/good_wallet.txt"
            }.get(operation_type)

            failed_file = {
                "reg": "result/bad_reg.txt",
                "auth": "result/bad_auth.txt",
                "farm": "result/bad_farm.txt",
                "connect_wallet": "result/bad_wallet.txt"
            }.get(operation_type)

            # Save successful accounts
            if success_accounts:
                with open(success_file, 'w', encoding='utf-8') as f:
                    for account in success_accounts:
                        if operation_type == 'connect_wallet':
                            f.write(f"{account['Email']}:{account['Password']}:{account['PrivateKey']}\n")
                        else:
                            f.write(f"{account['Email']}:{account['Password']}\n")
                self.log(f"{Fore.GREEN}Successful accounts saved to {success_file}{Style.RESET_ALL}")

            # Save failed accounts
            if failed_accounts:
                with open(failed_file, 'w', encoding='utf-8') as f:
                    for account in failed_accounts:
                        if operation_type == 'connect_wallet':
                            f.write(f"{account['Email']}:{account['Password']}:{account['PrivateKey']}\n")
                        else:
                            f.write(f"{account['Email']}:{account['Password']}\n")
                self.log(f"{Fore.YELLOW}Failed accounts saved to {failed_file}{Style.RESET_ALL}")

        except Exception as e:
            self.log(f"{Fore.RED}Error saving results: {str(e)}{Style.RESET_ALL}")
    
    def print_question(self):
        while True:
            try:
                print("1. Registration")
                print("2. Authorization")
                print("3. Farm")
                print("4. Connect Wallet")
                print("5. Check Airdrop")
                choose = int(input("Choose action [1/2/3/4/5] -> ").strip())

                if choose in [1, 2, 3, 4, 5]:
                    action_type = (
                        "Registration" if choose == 1 else 
                        "Authorization" if choose == 2 else 
                        "Farm" if choose == 3 else
                        "Connect Wallet" if choose == 4 else
                        "Check Airdrop"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Selected: {action_type}{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter a number from 1 to 5.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, 3, 4 or 5).{Style.RESET_ALL}")

    async def load_proxies(self):
        """Loading proxies from proxy.txt file"""
        filename = "data/proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} not found.{Style.RESET_ALL}")
                return
                
            with open(filename, 'r') as f:
                self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No proxies found in file.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Loaded proxies: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Error loading proxies: {str(e)}{Style.RESET_ALL}")

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, email):
        if email not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[email] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[email]

    def rotate_proxy_for_account(self, email):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[email] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def mask_account(self, account):
        if "@" in account:
            local, domain = account.split('@', 1)
            mask_account = local[:3] + '*' * 3 + local[-3:]
            return f"{mask_account}@{domain}"
    
    def print_message(self, email, proxy, color, message):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}[ Account:{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(email) if email else 'N/A'} {Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT} Proxy: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{proxy if proxy else 'None'}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
            f"{color + Style.BRIGHT} {message} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
        )

    async def user_login(self, email: str, password: str, proxy=None):
        try:
            # Getting captcha token
            captcha_token = await self.captcha_solver.solve_captcha()
            if not captcha_token:
                self.print_message(email, proxy, Fore.RED, "Failed to solve captcha")
                return None
                
            url = "https://api.openloop.so/users/login"
            data = json.dumps({"username":email, "password":password})
            headers = {
                **self.headers,
                "Authorization": "Bearer",
                "Content-Length": str(len(data)),
                "Content-Type": "text/plain;charset=UTF-8",
                "x-recaptcha-response": captcha_token
            }
            connector = ProxyConnector.from_url(proxy) if proxy else None
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result['data']['accessToken']
        except (Exception, ClientResponseError) as e:
            self.print_message(email, proxy, Fore.RED, f"Error getting access token: {Fore.YELLOW+Style.BRIGHT}{str(e)}")
            return None

    async def user_register(self, email: str, password: str, proxy=None):
        try:
            # Getting captcha token
            captcha_token = await self.captcha_solver.solve_captcha()
            if not captcha_token:
                self.print_message(email, proxy, Fore.RED, "Failed to solve captcha")
                return False
                
            url = "https://api.openloop.so/users/register"
            # Using email as username
            name = email.split('@')[0]  # Use part before @ as name
            data = json.dumps({
                "name": name,
                "username": email,
                "password": password,
                "inviteCode": INVITE_CODE
            })
            
            headers = {
                **self.headers,
                "Content-Length": str(len(data)),
                "Content-Type": "application/json",
                "x-recaptcha-response": captcha_token
            }
            
            connector = ProxyConnector.from_url(proxy) if proxy else None
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                try:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        result = await response.json()
                        
                        # Check for successful registration (code 2000 is also success)
                        if result.get("code") in [200, 2000] or result.get("message") == "Success":
                            self.print_message(email, proxy, Fore.GREEN, "Registration successful")
                            return True
                        
                        # If account already exists, consider it a success
                        # Check only for message "account already exists", regardless of code
                        elif "account already exists" in str(result).lower():
                            self.print_message(email, proxy, Fore.YELLOW, "Account already exists (considered successful)")
                            return True
                        else:
                            self.print_message(email, proxy, Fore.RED, f"Registration failed: {result.get('message', 'Unknown error')}")
                            return False
                except ClientResponseError as e:
                    # Check for any error with message about existing account
                    if "account already exists" in str(e).lower():
                        self.print_message(email, proxy, Fore.YELLOW, "Account already exists (considered successful)")
                        return True
                    raise e
        except (Exception, ClientResponseError) as e:
            # Also check here for string about existing account
            if "account already exists" in str(e).lower():
                self.print_message(email, proxy, Fore.YELLOW, "Account already exists (considered successful)")
                return True
            
            self.print_message(email, proxy, Fore.RED, f"Registration error: {Fore.YELLOW+Style.BRIGHT}{str(e)}")
            return False
        
    async def mission_lists(self, email: str, password: str, token: str, use_proxy: bool, proxy=None, retries=MAX_RETRIES):
        url = "https://api.openloop.so/missions"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        if response.status == 401:
                            token = await self.get_access_token(email, password, use_proxy)
                            headers["Authorization"] = f"Bearer {token}"
                            continue

                        response.raise_for_status()
                        result = await response.json()
                        return result['data']['missions']
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                
                self.print_message(email, proxy, Fore.RED, f"Error getting available missions: {Fore.YELLOW+Style.BRIGHT}{str(e)}")
                return None
        
    async def complete_missions(self, email: str, password: str, token: str, mission_id: int, use_proxy: bool, proxy=None, retries=MAX_RETRIES):
        url = f"https://api.openloop.so/missions/{mission_id}/complete"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        if response.status == 401:
                            token = await self.get_access_token(email, password, use_proxy)
                            headers["Authorization"] = f"Bearer {token}"
                            continue

                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                
                self.print_message(email, proxy, Fore.RED, f"Error completing mission: {Fore.YELLOW+Style.BRIGHT}{str(e)}")
                return None
            
    async def send_ping(self, email: str, password: str, token: str, quality: int, use_proxy: bool, proxy=None, retries=MAX_RETRIES):
        url = "https://api.openloop.so/bandwidth/share"
        data = json.dumps({"quality":quality})
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        if response.status == 401:
                            token = await self.get_access_token(email, password, use_proxy)
                            headers["Authorization"] = f"Bearer {token}"
                            continue

                        response.raise_for_status()
                        result = await response.json()
                        return result['data']
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                self.print_message(email, proxy, Fore.RED, f"Error sending PING: {Fore.YELLOW+Style.BRIGHT}{str(e)}")

                if "invalid proxy response" in str(e).lower():
                    proxy = self.rotate_proxy_for_account(email) if use_proxy else None

                return None
            
    async def get_access_token(self, email: str, password: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(email) if use_proxy else None
        try:
            token = await self.user_login(email, password, proxy)
            if token:
                self.print_message(email, proxy, Fore.GREEN, "Successfully obtained access token")
                self.save_token(email, token)
                return token
            return None  # If token is None, there was an authentication error
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                self.print_message(email, proxy, Fore.RED, "Invalid credentials")
                return None
            self.print_message(email, proxy, Fore.RED, f"Error: {str(e)}")
            return None
            
    def save_token(self, email: str, token: str):
        """Saves authorization token to accounts.json file"""
        try:
            # Create data directory if it doesn't exist
            if not os.path.exists('data'):
                os.makedirs('data')
                
            data = {}
            if os.path.exists('data/accounts.json'):
                try:
                    with open('data/accounts.json', 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        if file_content:  # Check that the file is not empty
                            data = json.loads(file_content)
                except (json.JSONDecodeError, ValueError):
                    # If the file contains invalid JSON, start with an empty dictionary
                    self.log(f"{Fore.YELLOW}File accounts.json contains invalid JSON. Creating new file.{Style.RESET_ALL}")
                    data = {}
            
            data[email] = {"token": token}
            
            with open('data/accounts.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            self.print_message(email, None, Fore.GREEN, "Token successfully saved")
        except Exception as e:
            self.print_message(email, None, Fore.RED, f"Error saving token: {str(e)}")

    def get_saved_token(self, email: str) -> str:
        """Gets saved token from accounts.json for the specified email"""
        try:
            if os.path.exists('data/accounts.json'):
                with open('data/accounts.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if email in data and "token" in data[email]:
                        return data[email]["token"]
        except Exception as e:
            self.log(f"{Fore.RED}Error reading token: {str(e)}{Style.RESET_ALL}")
        return None
        
    async def process_complete_missions(self, email: str, password: str, token: str, use_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None
            missions = await self.mission_lists(email, password, token, use_proxy, proxy)
            if missions:
                completed = False
                for mission in missions:
                    mission_id = str(mission['missionId'])
                    title = mission['name']
                    reward = mission['reward']['amount']
                    type = mission['reward']['type']
                    status = mission['status']

                    if mission and status == "available":
                        complete = await self.complete_missions(email, password, token, mission_id, use_proxy, proxy)
                        if complete and "message" in complete and complete['message'] == "Success":
                            self.print_message(email, proxy, Fore.WHITE, 
                                f"Mission {title}"
                                f"{Fore.GREEN + Style.BRIGHT} completed {Style.RESET_ALL}"
                                f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                                f"{Fore.CYAN + Style.BRIGHT} Reward: {Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT}{reward} {type}{Style.RESET_ALL}"
                            )
                        else:
                            self.print_message(email, proxy, Fore.WHITE, 
                                f"Mission {title} "
                                f"{Fore.RED + Style.BRIGHT}not completed{Style.RESET_ALL}"
                            )
                        await asyncio.sleep(1)

                    else:
                        completed = True

                if completed:
                    self.print_message(email, proxy, Fore.GREEN, 
                        "All available missions completed"
                    )

            await asyncio.sleep(24 * 60 * 60)  # Check missions once a day

    async def process_send_ping(self, email: str, password: str, token: str, use_proxy: bool):
        quality = random.randint(60, 80)
        while True:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Attempting to send PING...{Style.RESET_ALL}                                         ",
                end="\r",
                flush=True
            )

            ping = await self.send_ping(email, password, token, quality, use_proxy, proxy)
            if ping:
                total_earning = ping.get('balances', {}).get('POINT', 0)
                self.print_message(email, proxy, Fore.GREEN, 
                    "PING successfully sent "
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.CYAN + Style.BRIGHT} Earned: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}Total {total_earning:.2f} PTS{Style.RESET_ALL}"
                )

            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Waiting 15 minutes until next PING...{Style.RESET_ALL}",
                end="\r"
            )
            await asyncio.sleep(15 * 60)  # Send ping every 15 minutes
            
    async def process_accounts(self, email: str, password: str, use_proxy: bool):
        """Process individual account: authorization and start farm tasks"""
        token = self.get_saved_token(email)
        if token:
            self.print_message(email, None, Fore.GREEN, "Token loaded from accounts.json")
        else:
            token = await self.get_access_token(email, password, use_proxy)
        
        if token:
            tasks = []
            tasks.append(self.process_complete_missions(email, password, token, use_proxy))
            tasks.append(self.process_send_ping(email, password, token, use_proxy))
            await asyncio.gather(*tasks)
    
    async def process_auth_batch(self, accounts_batch, use_proxy):
        """Process a batch of accounts for authorization"""
        tasks = []
        failed_accounts = []
        success_accounts = []
        
        for account in accounts_batch:
            email = account.get('Email')
            password = account.get('Password')
            if "@" in email and password:
                tasks.append(self.get_access_token(email, password, use_proxy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for account, result in zip(accounts_batch, results):
            if isinstance(result, Exception) or not result:
                failed_accounts.append(account)
            elif result:
                success_accounts.append(account)
        
        return success_accounts, failed_accounts

    async def process_registration_batch(self, accounts_batch, use_proxy):
        """Process a batch of accounts for registration"""
        tasks = []
        failed_accounts = []
        success_accounts = []
        
        for account in accounts_batch:
            email = account.get('Email')
            password = account.get('Password')
            if "@" in email and password:
                proxy = self.get_next_proxy_for_account(email) if use_proxy else None
                tasks.append(self.user_register(email, password, proxy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for account, result in zip(accounts_batch, results):
            if isinstance(result, Exception) or not result:
                failed_accounts.append(account)
            elif result:
                success_accounts.append(account)
        
        return success_accounts, failed_accounts

    async def process_wallet_connect_batch(self, accounts_batch, use_proxy):
        """Process a batch of accounts for wallet connection"""
        tasks = []
        failed_accounts = []
        success_accounts = []
        
        for account in accounts_batch:
            email = account.get('Email')
            password = account.get('Password')
            private_key = account.get('PrivateKey')
            if email and password and private_key:
                tasks.append(self.process_connect_wallet(email, password, private_key, use_proxy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for account, result in zip(accounts_batch, results):
            if isinstance(result, Exception) or not result:
                failed_accounts.append(account)
            elif result:
                success_accounts.append(account)
        
        return success_accounts, failed_accounts

    async def process_connect_wallet(self, email: str, password: str, private_key: str, use_proxy: bool):
        """Process for connecting a wallet to a single account."""
        proxy = self.get_next_proxy_for_account(email) if use_proxy else None
        token = self.get_saved_token(email)
        if not token:
            token = await self.get_access_token(email, password, use_proxy)

        if not token:
            self.print_message(email, proxy, Fore.RED, "Could not get token, skipping wallet connection.")
            return False

        profile_data = await self.get_user_profile(token, proxy)
        if profile_data and profile_data.get("data", {}).get("address"):
            wallet_address = profile_data["data"]["address"]
            self.print_message(email, proxy, Fore.YELLOW, f"Wallet {wallet_address} already connected.")
            return True

        self.print_message(email, proxy, Fore.WHITE, "No wallet connected, proceeding to connect.")
        
        # Check for private key validity
        try:
            # For Solana, the private key is typically a base58 encoded string
            Keypair.from_base58_string(private_key)
        except Exception:
            self.print_message(email, proxy, Fore.RED, "Invalid private key provided.")
            return False

        success = await self.connect_wallet(token, private_key, proxy)
        if success:
            self.print_message(email, proxy, Fore.GREEN, "Wallet connected successfully.")
        else:
            self.print_message(email, proxy, Fore.RED, "Failed to connect wallet.")
        
        return success

    async def get_user_profile(self, token: str, proxy: str = None):
        """Fetches user profile to check for a connected wallet."""
        url = "https://api.openloop.so/users/profile"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except (Exception, ClientResponseError) as e:
            self.log(f"{Fore.RED}Error getting user profile: {e}{Style.RESET_ALL}")
            return None

    async def connect_wallet(self, token: str, private_key: str, proxy: str = None):
        """Connects a Solana wallet by signing a message and sending it to the server."""
        try:
            # 1. Prepare wallet and message
            message_to_sign = "Please sign this message to connect your wallet to OpenLoop and verifying your ownership only."
            keypair = Keypair.from_base58_string(private_key)
            wallet_address = str(keypair.pubkey())

            # 2. Sign the message
            # The solders library expects bytes, so we encode the message
            signature = keypair.sign_message(message_to_sign.encode('utf-8'))
            
            # 3. Prepare request payload and headers
            url = "https://api.openloop.so/users/link-wallet"
            payload = {
                "message": message_to_sign,
                "wallet": wallet_address,
                "signature": str(signature)  # Signature is base58 encoded by default
            }
            data = json.dumps(payload)
            headers = {
                **self.headers,
                "Authorization": f"Bearer {token}",
                "Content-Length": str(len(data)),
                "Content-Type": "application/json",
            }

            # 4. Send the request
            connector = ProxyConnector.from_url(proxy) if proxy else None
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    # Assuming a successful response contains a success message or specific code
                    if result.get("code") in [200, 2000] or result.get("message") == "Success":
                        return True
                    else:
                        self.log(f"{Fore.RED}Failed to link wallet, server response: {result}{Style.RESET_ALL}")
                        return False

        except (Exception, ClientResponseError) as e:
            self.log(f"{Fore.RED}An error occurred while connecting the wallet: {e}{Style.RESET_ALL}")
            return False

    async def get_airdrop_points(self, email: str, password: str, use_proxy: bool):
        """Получить количество airdrop поинтов для аккаунта"""
        proxy = self.get_next_proxy_for_account(email) if use_proxy else None
        token = self.get_saved_token(email)
        if not token:
            token = await self.get_access_token(email, password, use_proxy)
        if not token:
            return None, "no_token"
        url = "https://api.openloop.so/users/airdrop-point"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    result = await response.json()
                    if result.get("code") in [200, 2000]:
                        return result.get("data", 0), None
                    return None, "bad_response"
        except Exception as e:
            return None, str(e)

    async def process_airdrop_batch(self, accounts_batch, use_proxy):
        """Пакетная проверка airdrop поинтов"""
        tasks = []
        for account in accounts_batch:
            email = account.get('Email')
            password = account.get('Password')
            if email and password:
                tasks.append(self.get_airdrop_points(email, password, use_proxy))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        good, bad = [], []
        for account, result in zip(accounts_batch, results):
            if isinstance(result, Exception) or result[0] is None:
                bad.append(account)
            else:
                points = result[0]
                good.append({"Email": account["Email"], "Password": account["Password"], "Points": points})
        return good, bad

    def save_airdrop_results(self, good, bad):
        """Сохраняет результаты проверки airdrop"""
        if not os.path.exists('result'):
            os.makedirs('result')
        if good:
            with open('result/airdrop.txt', 'w', encoding='utf-8') as f:
                for acc in good:
                    f.write(f"{acc['Email']}:{acc['Password']}:{acc['Points']}\n")
        if bad:
            with open('result/bad_airdrop.txt', 'w', encoding='utf-8') as f:
                for acc in bad:
                    f.write(f"{acc['Email']}:{acc['Password']}\n")

    async def main(self):
        try:
            self.welcome()
            action_choice = self.print_question()

            # Registration
            if action_choice == 1:
                accounts = self.load_accounts("reg")
                if not accounts:
                    self.log(f"{Fore.RED+Style.BRIGHT}No accounts loaded from data/reg.txt{Style.RESET_ALL}")
                    return

                use_proxy = True
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Total accounts for registration: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies()

                self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

                failed_accounts = []
                success_accounts = []
                batch_size = min(MAX_REG_THREADS, len(accounts))
                total_batches = (len(accounts) + batch_size - 1) // batch_size
                total_accounts = len(accounts)

                self.log(f"{Fore.CYAN}Starting registration of {total_accounts} accounts in batches of {batch_size}{Style.RESET_ALL}")

                for i in range(0, len(accounts), batch_size):
                    current_batch = i // batch_size + 1
                    batch = list(islice(accounts, i, i + batch_size))
                    accounts_processed = min(i + batch_size, total_accounts)
                    self.log(
                        f"{Fore.CYAN}Processing batch {current_batch}/{total_batches} "
                        f"({len(batch)} accounts, progress: {accounts_processed}/{total_accounts}){Style.RESET_ALL}"
                    )
                    batch_success, batch_failed = await self.process_registration_batch(batch, use_proxy)
                    success_accounts.extend(batch_success)
                    failed_accounts.extend(batch_failed)

                # Save all results after processing all batches
                self.save_results("reg", success_accounts, failed_accounts)
                
                if failed_accounts:
                    self.log(f"{Fore.YELLOW}Failed registrations: {len(failed_accounts)}/{len(accounts)}{Style.RESET_ALL}")
                else:
                    self.log(f"{Fore.GREEN}All registrations successful!{Style.RESET_ALL}")
                return

            # Authorization
            if action_choice == 2:
                accounts = self.load_accounts("auth")
                if not accounts:
                    self.log(f"{Fore.RED+Style.BRIGHT}No accounts found in data/auth.txt or accounts.txt{Style.RESET_ALL}")
                    return

                use_proxy = True
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Total accounts for authorization: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies()  # Use local proxies

                self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

                failed_accounts = []
                success_accounts = []
                batch_size = min(MAX_AUTH_THREADS, len(accounts))
                total_batches = (len(accounts) + batch_size - 1) // batch_size
                total_accounts = len(accounts)
                
                self.log(f"{Fore.CYAN}Starting authorization of {total_accounts} accounts in batches of {batch_size}{Style.RESET_ALL}")
                
                for i in range(0, len(accounts), batch_size):
                    current_batch = i // batch_size + 1
                    batch = list(islice(accounts, i, i + batch_size))
                    accounts_processed = min(i + batch_size, total_accounts)
                    self.log(
                        f"{Fore.CYAN}Processing batch {current_batch}/{total_batches} "
                        f"({len(batch)} accounts, progress: {accounts_processed}/{total_accounts}){Style.RESET_ALL}"
                    )
                    batch_success, batch_failed = await self.process_auth_batch(batch, use_proxy)
                    success_accounts.extend(batch_success)
                    failed_accounts.extend(batch_failed)
                
                # Save all results after processing all batches
                self.save_results("auth", success_accounts, failed_accounts)
                
                if failed_accounts:
                    self.log(f"{Fore.YELLOW}Failed to authorize: {len(failed_accounts)}/{len(accounts)}{Style.RESET_ALL}")
                else:
                    self.log(f"{Fore.GREEN}All authorizations successful!{Style.RESET_ALL}")
                return

            # Connect Wallet
            if action_choice == 4:
                accounts = self.load_accounts("connect_wallet")
                if not accounts:
                    self.log(f"{Fore.RED+Style.BRIGHT}No accounts found in data/wallet.txt{Style.RESET_ALL}")
                    return

                use_proxy = True
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Total accounts for wallet connection: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies()

                self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

                failed_accounts = []
                success_accounts = []
                # Using MAX_AUTH_THREADS for batch size, can be changed to a new config var if needed
                batch_size = min(MAX_AUTH_THREADS, len(accounts))
                total_batches = (len(accounts) + batch_size - 1) // batch_size
                total_accounts = len(accounts)
                
                self.log(f"{Fore.CYAN}Starting wallet connection for {total_accounts} accounts in batches of {batch_size}{Style.RESET_ALL}")
                
                for i in range(0, len(accounts), batch_size):
                    current_batch = i // batch_size + 1
                    batch = list(islice(accounts, i, i + batch_size))
                    accounts_processed = min(i + batch_size, total_accounts)
                    self.log(
                        f"{Fore.CYAN}Processing batch {current_batch}/{total_batches} "
                        f"({len(batch)} accounts, progress: {accounts_processed}/{total_accounts}){Style.RESET_ALL}"
                    )
                    batch_success, batch_failed = await self.process_wallet_connect_batch(batch, use_proxy)
                    success_accounts.extend(batch_success)
                    failed_accounts.extend(batch_failed)
                
                self.save_results("connect_wallet", success_accounts, failed_accounts)
                
                if failed_accounts:
                    self.log(f"{Fore.YELLOW}Failed to connect wallets for: {len(failed_accounts)}/{len(accounts)}{Style.RESET_ALL}")
                else:
                    self.log(f"{Fore.GREEN}All wallet connections successful!{Style.RESET_ALL}")
                return

            # Check Airdrop
            if action_choice == 5:
                accounts = self.load_accounts("auth")
                if not accounts:
                    self.log(f"{Fore.RED+Style.BRIGHT}No accounts found in data/auth.txt or accounts.txt{Style.RESET_ALL}")
                    return
                use_proxy = True
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Total accounts for airdrop check: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )
                if use_proxy:
                    await self.load_proxies()
                self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)
                batch_size = min(MAX_AUTH_THREADS, len(accounts))
                total_batches = (len(accounts) + batch_size - 1) // batch_size
                total_accounts = len(accounts)
                self.log(f"{Fore.CYAN}Starting airdrop check for {total_accounts} accounts in batches of {batch_size}{Style.RESET_ALL}")
                good, bad = [], []
                for i in range(0, len(accounts), batch_size):
                    current_batch = i // batch_size + 1
                    batch = list(islice(accounts, i, i + batch_size))
                    accounts_processed = min(i + batch_size, total_accounts)
                    self.log(
                        f"{Fore.CYAN}Processing batch {current_batch}/{total_batches} "
                        f"({len(batch)} accounts, progress: {accounts_processed}/{total_accounts}){Style.RESET_ALL}"
                    )
                    batch_good, batch_bad = await self.process_airdrop_batch(batch, use_proxy)
                    good.extend(batch_good)
                    bad.extend(batch_bad)
                self.save_airdrop_results(good, bad)
                self.log(f"{Fore.GREEN}Airdrop check complete. Good: {len(good)}, Bad: {len(bad)}{Style.RESET_ALL}")
                return

            # Farming
            accounts = self.load_accounts("farm")
            if not accounts:
                accounts = self.load_accounts()  # Try to load from accounts.txt if farm.txt not found
                if not accounts:
                    self.log(f"{Fore.RED+Style.BRIGHT}No accounts found in data/farm.txt or accounts.txt{Style.RESET_ALL}")
                    return

            use_proxy = True
            self.clear_terminal()
            self.welcome()
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Total accounts for farming: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
            )

            if use_proxy:
                await self.load_proxies()  # Use local proxies

            self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

            while True:
                tasks = []
                for account in accounts:
                    email = account.get('Email')
                    password = account.get('Password')

                    if "@" in email and password:
                        tasks.append(self.process_accounts(email, password, use_proxy))

                await asyncio.gather(*tasks)
                await asyncio.sleep(10)

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        async def run():
            bot = OpenLoop()
            await bot.start()
            try:
                await bot.main()
            finally:
                await bot.stop()
        
        asyncio.run(run())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] OpenLoop - BOT{Style.RESET_ALL}                                       "                              
        )