<div align="center">

  <p align="center">
    <a href="https://t.me/cry_batya">
      <img src="https://img.shields.io/badge/Telegram-Channel-blue?style=for-the-badge&logo=telegram" alt="Telegram Channel">
    </a>
    <a href="https://t.me/+b0BPbs7V1aE2NDFi">
      <img src="https://img.shields.io/badge/Telegram-Chat-blue?style=for-the-badge&logo=telegram" alt="Telegram Chat">
    </a>
  </p>
</div>

# OpenLoop Community Node BOT

- Register Here : [OpenLoop Community Node Dashboard](https://openloop.so/auth/register)
- Download Extension Here : [OpenLoop Community Node Extension](https://chromewebstore.google.com/detail/openloop-community-node/effapmdildnpkiaeghlkicpfflpiambm)
- Use Code : ol95e4a7e2

## Features

  - Auto Registration
  - Auto Authorization and Token Management
  - Auto Get Account Information
  - Auto Claim Rewards
  - Auto Complete Available Missions
  - Auto Send Ping Every 3 Minutes
  - Multi Accounts With Threads
  - Proxy Support for All Operations
  - Smart Token Management System
  - Support for Multiple Captcha Solvers (2captcha, CapMonster, AntiCaptcha, CFLSolver)
  - Auto Connect Solana Wallet

## Requirements

- Make sure you have Python3.9 or higher installed and pip.
- Required Python packages (installed via requirements.txt):


## Installation

1. **Clone The Repository:**
   ```bash
   git clone https://github.com/TellBip/OpenLoop.git
   ```
   ```bash
   cd OpenLoop
   ```

2. **Install Requirements:**
   ```bash
   pip install -r requirements.txt #or pip3 install -r requirements.txt
   ```

3. **For CFLSolver (Optional):**
   If you want to use the Turnstile-Solver (CFLSolver), you need to install and run it:
   ```bash
   git clone https://github.com/Theyka/Turnstile-Solver.git
   cd Turnstile-Solver
   pip install -r requirements.txt
   python -m patchright install chromium
   python api_solver.py
   ```
   For more information, see the [Turnstile-Solver repository](https://github.com/Theyka/Turnstile-Solver).

## Configuration

1. **Create data folder:**
   ```bash
   mkdir data
   ```

2. **Registration accounts:** Create `data/reg.txt` for registration with format:
   ```
   email1@example.com:password1
   email2@example.com:password2
   ```

3. **Authorization accounts:** Create `data/auth.txt` for authorization with format:
   ```
   email1@example.com:password1
   email2@example.com:password2
   ```

4. **Farming accounts:** Create `data/farm.txt` for farming with format:
   ```
   email1@example.com:password1
   email2@example.com:password2
   ```

5. **Wallet connecting accounts:** Create `data/wallet.txt` for connecting wallets with format:
   ```
   email1@example.com:password1:your_solana_private_key_in_base58
   email2@example.com:password2:your_solana_private_key_in_base58
   ```

6. **proxy.txt:** Create `data/proxy.txt` with your proxies in the following format:
   ```
   ip:port # Default Protocol HTTP
   protocol://ip:port
   protocol://user:pass@ip:port
   ```
   Supported protocols: http, https, socks4, socks5

7. **config.py:** Configure captcha service and threads in `core/config.py`:
   ```python
   # Captcha service settings
   CAPTCHA_SERVICE = "2captcha"  # Available: 2captcha, capmonster, anticaptcha, cflsolver
   CAPTCHA_API_KEY = "your_api_key"  # API key for the service
   CFLSOLVER_BASE_URL = "http://localhost:5000"  # URL for local CFLSolver API

   CAPTCHA_WEBSITE_KEY = "0x4AAAAAAA3AMTe5gwdZnIEL"  # Cloudflare Turnstile key
   CAPTCHA_WEBSITE_URL = "https://openloop.so"  # Site URL for captcha

   # Authorization settings
   MAX_AUTH_THREADS = 5  # Maximum threads for authorization
   MAX_REG_THREADS = 3   # Maximum threads for registration
   MAX_RETRIES = 3       # Maximum number of retries for API requests

   INVITE_CODE = "ol95e4a7e2"  # Referral code
   ```

### Helper script for data preparation (`dop/merge_data.py`)

To simplify the creation of `wallet.txt`, you can use the helper script located in the `dop` folder.

1.  Place your source files inside the `dop` folder:
    -   `email.txt` with the format `email:password`.
    -   `private_keys.txt` with one Solana private key (in base58 format) per line.
2.  Make sure the number of lines in both files is the same.
3.  Navigate to the `dop` directory and run the script:
    ```bash
    cd dop
    python merge_data.py
    ```
4.  The script will generate a `wallet.txt` file in the `dop` folder. Move this file to the main `data` directory (`mv wallet.txt ../data/`) for the bot to use.


## Usage

Run the bot:
```bash
python main.py #or python3 main.py
```

The bot has 4 modes:
1. Registration
   - Registers accounts using INVITE_CODE from config
   - Handles already registered accounts properly
   - Saves successful registrations to result/good_reg.txt
   - Saves failed registrations to result/bad_reg.txt

2. Authorization
   - Gets and saves tokens
   - Saves successful authorizations to result/good_auth.txt
   - Saves failed authorizations to result/bad_auth.txt

3. Farming
   - Automatically sends ping every 3 minutes
   - Completes available missions
   - Shows earnings in real-time
   - Automatic reconnection on errors

4. Connect Wallet
   - Connects Solana wallets to accounts using data from `data/wallet.txt`.
   - Checks if a wallet is already connected before attempting to link a new one.
   - Saves results to `result/good_wallet.txt` and `result/bad_wallet.txt`.

## Results

The bot creates a `result` folder with the following files:
- good_reg.txt: Successfully registered accounts
- bad_reg.txt: Failed registration attempts
- good_auth.txt: Successfully authorized accounts
- bad_auth.txt: Failed authorization attempts
- good_farm.txt: Successfully farming accounts
- bad_farm.txt: Failed farming attempts
- good_wallet.txt: Accounts with successfully connected wallets
- bad_wallet.txt: Accounts where wallet connection failed

Tokens are stored in `data/accounts.json` for future use.

## Telegram http://t.me/+1fc0or8gCHsyNGFi

Thank you for visiting this repository, don't forget to contribute in the form of follows and stars.
If you have questions, find an issue, or have suggestions for improvement, feel free to contact me or open an *issue* in this GitHub repository.
