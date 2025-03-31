# Captcha service settings
CAPTCHA_SERVICE = "cflsolver"  # Captcha solving service (available: 2captcha, capmonster, anticaptcha, cflsolver)
CAPTCHA_API_KEY = "api"  # API key for the service

CFLSOLVER_BASE_URL = "http://Host:5000"  # URL для локального API CFLSolver

CAPTCHA_WEBSITE_KEY = "0x4AAAAAAA3AMTe5gwdZnIEL"  # Ключ Cloudflare Turnstile капчи
CAPTCHA_WEBSITE_URL = "https://openloop.so"  # URL сайта для капчи

# Authorization settings
MAX_AUTH_THREADS = 2  # Maximum number of concurrent authorization threads
MAX_REG_THREADS = 3   # Maximum number of concurrent registration threads (lower due to email verification)
MAX_RETRIES = 3      # Maximum number of retries for API requests

INVITE_CODE = "ol95e4a7e2"  # Invite code for registration