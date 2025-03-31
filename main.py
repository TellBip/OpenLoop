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

# Устанавливаем временную зону
wib = pytz.timezone('Asia/Jakarta')

# Инициализация colorama для Windows
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
        
        # Инициализация сервиса капчи
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
            raise ValueError(f"Неподдерживаемый сервис капчи: {CAPTCHA_SERVICE}")

    async def start(self):
        """Инициализация сессии"""
        if self.session is None:
            self.session = ClientSession()
        return self

    async def stop(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
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
        """Загружает аккаунты на основе типа операции (reg/auth/farm)"""
        filename = {
            "reg": "data/reg.txt",
            "auth": "data/auth.txt",
            "farm": "data/farm.txt"
        }.get(operation_type, "accounts.txt")

        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}Файл '{filename}' не найден.{Style.RESET_ALL}")
                return []
            accounts = []
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line and ':' in line:
                        email, password = line.split(':', 1)
                        accounts.append({"Email": email.strip(), "Password": password.strip()})
            return accounts
        except Exception as e:
            self.log(f"{Fore.RED}Ошибка загрузки аккаунтов: {e}{Style.RESET_ALL}")
            return []
    
    def save_results(self, operation_type: str, success_accounts: list, failed_accounts: list):
        """Сохраняет результаты операций в соответствующие файлы"""
        try:
            if not os.path.exists('result'):
                os.makedirs('result')

            # Определяем имена файлов на основе типа операции
            success_file = {
                "reg": "result/good_reg.txt",
                "auth": "result/good_auth.txt",
                "farm": "result/good_farm.txt"
            }.get(operation_type)

            failed_file = {
                "reg": "result/bad_reg.txt",
                "auth": "result/bad_auth.txt",
                "farm": "result/bad_farm.txt"
            }.get(operation_type)

            # Сохраняем успешные аккаунты
            if success_accounts:
                with open(success_file, 'w', encoding='utf-8') as f:
                    for account in success_accounts:
                        f.write(f"{account['Email']}:{account['Password']}\n")
                self.log(f"{Fore.GREEN}Успешные аккаунты сохранены в {success_file}{Style.RESET_ALL}")

            # Сохраняем неудачные аккаунты
            if failed_accounts:
                with open(failed_file, 'w', encoding='utf-8') as f:
                    for account in failed_accounts:
                        f.write(f"{account['Email']}:{account['Password']}\n")
                self.log(f"{Fore.YELLOW}Неудачные аккаунты сохранены в {failed_file}{Style.RESET_ALL}")

        except Exception as e:
            self.log(f"{Fore.RED}Ошибка сохранения результатов: {str(e)}{Style.RESET_ALL}")
    
    def print_question(self):
        while True:
            try:
                print("1. Registration")
                print("2. Authorization")
                print("3. Farm")
                choose = int(input("Choose action [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    action_type = (
                        "Registration" if choose == 1 else 
                        "Authorization" if choose == 2 else 
                        "Farm"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Selected: {action_type}{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter a number from 1 to 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

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
            f"{Fore.CYAN + Style.BRIGHT}[ Аккаунт:{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(email) if email else 'N/A'} {Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT} Прокси: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{proxy if proxy else 'Нет'}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}Статус:{Style.RESET_ALL}"
            f"{color + Style.BRIGHT} {message} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
        )

    async def user_login(self, email: str, password: str, proxy=None):
        try:
            # Получаем токен капчи
            captcha_token = await self.captcha_solver.solve_captcha()
            if not captcha_token:
                self.print_message(email, proxy, Fore.RED, "Не удалось решить капчу")
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
            self.print_message(email, proxy, Fore.RED, f"Ошибка получения токена доступа: {Fore.YELLOW+Style.BRIGHT}{str(e)}")
            return None

    async def user_register(self, email: str, password: str, proxy=None):
        try:
            # Получаем токен капчи
            captcha_token = await self.captcha_solver.solve_captcha()
            if not captcha_token:
                self.print_message(email, proxy, Fore.RED, "Не удалось решить капчу")
                return False
                
            url = "https://api.openloop.so/users/register"
            # Используем email в качестве имени пользователя и username
            name = email.split('@')[0]  # Используем часть до @ в качестве имени
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
                        
                        # Проверяем на успешную регистрацию
                        if result.get("code") == 200 and result.get("message") == "Success":
                            self.print_message(email, proxy, Fore.GREEN, "Registration successful")
                            return True
                        
                        # Если аккаунт уже существует, считаем это успешным результатом
                        # Проверяем только на наличие сообщения "account already exists", независимо от кода
                        elif "account already exists" in str(result).lower():
                            self.print_message(email, proxy, Fore.YELLOW, "Account already exists (considered successful)")
                            return True
                        else:
                            self.print_message(email, proxy, Fore.RED, f"Registration failed: {result.get('message', 'Unknown error')}")
                            return False
                except ClientResponseError as e:
                    # Проверяем на любую ошибку с сообщением о существующем аккаунте
                    if "account already exists" in str(e).lower():
                        self.print_message(email, proxy, Fore.YELLOW, "Account already exists (considered successful)")
                        return True
                    raise e
        except (Exception, ClientResponseError) as e:
            # Также проверяем и здесь на строку об уже существующем аккаунте
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
                
                self.print_message(email, proxy, Fore.RED, f"Ошибка получения доступных миссий: {Fore.YELLOW+Style.BRIGHT}{str(e)}")
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
                
                self.print_message(email, proxy, Fore.RED, f"Ошибка выполнения миссии: {Fore.YELLOW+Style.BRIGHT}{str(e)}")
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

                self.print_message(email, proxy, Fore.RED, f"Ошибка отправки PING: {Fore.YELLOW+Style.BRIGHT}{str(e)}")

                if "invalid proxy response" in str(e).lower():
                    proxy = self.rotate_proxy_for_account(email) if use_proxy else None

                return None
            
    async def get_access_token(self, email: str, password: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(email) if use_proxy else None
        try:
            token = await self.user_login(email, password, proxy)
            if token:
                self.print_message(email, proxy, Fore.GREEN, "Успешно получен токен доступа")
                self.save_token(email, token)
                return token
            return None  # Если token None, значит была ошибка авторизации
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                self.print_message(email, proxy, Fore.RED, "Неверные учетные данные")
                return None
            self.print_message(email, proxy, Fore.RED, f"Ошибка: {str(e)}")
            return None
            
    def save_token(self, email: str, token: str):
        """Сохраняет токен авторизации в файл accounts.json"""
        try:
            # Создаем директорию data, если она не существует
            if not os.path.exists('data'):
                os.makedirs('data')
                
            data = {}
            if os.path.exists('data/accounts.json'):
                try:
                    with open('data/accounts.json', 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        if file_content:  # Проверяем, что файл не пустой
                            data = json.loads(file_content)
                except (json.JSONDecodeError, ValueError):
                    # Если файл содержит некорректный JSON, начинаем с пустого словаря
                    self.log(f"{Fore.YELLOW}File accounts.json contains invalid JSON. Creating new file.{Style.RESET_ALL}")
                    data = {}
            
            data[email] = {"token": token}
            
            with open('data/accounts.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            self.print_message(email, None, Fore.GREEN, "Token successfully saved")
        except Exception as e:
            self.print_message(email, None, Fore.RED, f"Error saving token: {str(e)}")

    def get_saved_token(self, email: str) -> str:
        """Получает сохраненный токен из accounts.json для указанного email"""
        try:
            if os.path.exists('data/accounts.json'):
                with open('data/accounts.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if email in data and "token" in data[email]:
                        return data[email]["token"]
        except Exception as e:
            self.log(f"{Fore.RED}Ошибка при чтении токена: {str(e)}{Style.RESET_ALL}")
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
                                f"Миссия {title}"
                                f"{Fore.GREEN + Style.BRIGHT} выполнена {Style.RESET_ALL}"
                                f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                                f"{Fore.CYAN + Style.BRIGHT} Награда: {Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT}{reward} {type}{Style.RESET_ALL}"
                            )
                        else:
                            self.print_message(email, proxy, Fore.WHITE, 
                                f"Миссия {title} "
                                f"{Fore.RED + Style.BRIGHT}не выполнена{Style.RESET_ALL}"
                            )
                        await asyncio.sleep(1)

                    else:
                        completed = True

                if completed:
                    self.print_message(email, proxy, Fore.GREEN, 
                        "Все доступные миссии выполнены"
                    )

            await asyncio.sleep(24 * 60 * 60)  # Проверяем миссии раз в сутки

    async def process_send_ping(self, email: str, password: str, token: str, use_proxy: bool):
        quality = random.randint(60, 80)
        while True:
            proxy = self.get_next_proxy_for_account(email) if use_proxy else None
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Попытка отправки PING...{Style.RESET_ALL}                                         ",
                end="\r",
                flush=True
            )

            ping = await self.send_ping(email, password, token, quality, use_proxy, proxy)
            if ping:
                total_earning = ping.get('balances', {}).get('POINT', 0)
                self.print_message(email, proxy, Fore.GREEN, 
                    "PING успешно отправлен "
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.CYAN + Style.BRIGHT} Заработано: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}Всего {total_earning:.2f} PTS{Style.RESET_ALL}"
                )

            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Ожидание 3 минуты до следующего PING...{Style.RESET_ALL}",
                end="\r"
            )
            await asyncio.sleep(3 * 60)  # Отправляем пинг каждые 3 минуты
            
    async def process_accounts(self, email: str, password: str, use_proxy: bool):
        """Обрабатывает отдельный аккаунт: авторизация и запуск farm задач"""
        token = self.get_saved_token(email)
        if token:
            self.print_message(email, None, Fore.GREEN, "Токен загружен из accounts.json")
        else:
            token = await self.get_access_token(email, password, use_proxy)
        
        if token:
            tasks = []
            tasks.append(self.process_complete_missions(email, password, token, use_proxy))
            tasks.append(self.process_send_ping(email, password, token, use_proxy))
            await asyncio.gather(*tasks)
    
    async def process_auth_batch(self, accounts_batch, use_proxy):
        """Обрабатывает пакет аккаунтов для авторизации"""
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
        
        # Сохраняем результаты
        self.save_results("auth", success_accounts, failed_accounts)
        return failed_accounts

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
        
        # Save results
        self.save_results("reg", success_accounts, failed_accounts)
        return failed_accounts

    async def main(self):
        try:
            self.welcome()
            action_choice = self.print_question()

            # Регистрация
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
                    batch_failed = await self.process_registration_batch(batch, use_proxy)
                    failed_accounts.extend(batch_failed)

                if failed_accounts:
                    self.log(f"{Fore.YELLOW}Failed registrations: {len(failed_accounts)}/{len(accounts)}{Style.RESET_ALL}")
                else:
                    self.log(f"{Fore.GREEN}All registrations successful!{Style.RESET_ALL}")
                return

            # Авторизация
            if action_choice == 2:
                accounts = self.load_accounts("auth")
                if not accounts:
                    self.log(f"{Fore.RED+Style.BRIGHT}Аккаунты не найдены в data/auth.txt или accounts.txt{Style.RESET_ALL}")
                    return

                use_proxy = True
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Всего аккаунтов для авторизации: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies()  # Используем локальные прокси

                self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

                failed_accounts = []
                batch_size = min(MAX_AUTH_THREADS, len(accounts))
                total_batches = (len(accounts) + batch_size - 1) // batch_size
                total_accounts = len(accounts)
                
                self.log(f"{Fore.CYAN}Начинаем авторизацию {total_accounts} аккаунтов батчами по {batch_size}{Style.RESET_ALL}")
                
                for i in range(0, len(accounts), batch_size):
                    current_batch = i // batch_size + 1
                    batch = list(islice(accounts, i, i + batch_size))
                    accounts_processed = min(i + batch_size, total_accounts)
                    self.log(
                        f"{Fore.CYAN}Обработка батча {current_batch}/{total_batches} "
                        f"({len(batch)} аккаунтов, прогресс: {accounts_processed}/{total_accounts}){Style.RESET_ALL}"
                    )
                    batch_failed = await self.process_auth_batch(batch, use_proxy)
                    failed_accounts.extend(batch_failed)
                
                if failed_accounts:
                    self.log(f"{Fore.YELLOW}Не удалось авторизовать: {len(failed_accounts)}/{len(accounts)}{Style.RESET_ALL}")
                else:
                    self.log(f"{Fore.GREEN}Все авторизации успешны!{Style.RESET_ALL}")
                return

            # Фарминг
            accounts = self.load_accounts("farm")
            if not accounts:
                accounts = self.load_accounts()  # Пробуем загрузить из accounts.txt если farm.txt не найден
                if not accounts:
                    self.log(f"{Fore.RED+Style.BRIGHT}Аккаунты не найдены в data/farm.txt или accounts.txt{Style.RESET_ALL}")
                    return

            use_proxy = True
            self.clear_terminal()
            self.welcome()
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Всего аккаунтов для фарминга: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
            )

            if use_proxy:
                await self.load_proxies()  # Используем локальные прокси

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
            self.log(f"{Fore.RED+Style.BRIGHT}Ошибка: {e}{Style.RESET_ALL}")

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