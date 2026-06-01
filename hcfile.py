install_requires = [

    # ── Core Framework ─────────────────────────────────────────
    "Django>=5.2",
    "asgiref>=3.10",          # Django dependency
    "sqlparse>=0.5",          # Django dependency

    # ── Database ───────────────────────────────────────────────
    "PyMySQL>=2.2",           # MySQL connector  (db_manager.py)
    "oracledb>=4.0",          # Oracle connector (oracle_manager.py)

    # ── Scheduler ──────────────────────────────────────────────
    "APScheduler>=3.11",      # DateTrigger chain (scheduler_service.py)
    "croniter>=6.0",          # cron expression parsing

    # ── Excel Reports ──────────────────────────────────────────
    "openpyxl>=3.1",          # Excel generation (excel_generator.py)

    # ── Encryption ─────────────────────────────────────────────
    "cryptography>=48.0",     # AES password encryption (crypto.py)

    # ── Frontend ───────────────────────────────────────────────
    "django-bootstrap5>=25.3",

    # ── Audit ──────────────────────────────────────────────────
    "django-easy-audit>=1.3",

    # ── Timezone ───────────────────────────────────────────────
    "pytz>=2026.2",
    "tzdata>=2025.2",

    # ── Windows Only ───────────────────────────────────────────
    "pywin32>=311;platform_system=='Windows'",   # pythoncom (scheduler_service.py)
    "WMI>=1.5;platform_system=='Windows'",       # server checks (server_manager.py)
]







# ── Django Q (separate task queue project) ──────────────────
django-q2==1.8.0
django-picklefield==3.4.0

# ── Redis (Django Q broker) ─────────────────────────────────
redis==7.0.1

# ── Web Server ───────────────────────────────────────────────
mod_wsgi==5.0.2

# ── System / Process monitoring ──────────────────────────────
psutil==7.1.3

# ── Terminal / CLI display ────────────────────────────────────
blessed==1.23.0
ansicon==1.89.0
jinxed==1.3.0
wcwidth==0.2.14

# ── Excel (alternate, not used by HC) ────────────────────────
xlsxwriter==3.2.9

# ── Crypto (alternate, not used by HC) ───────────────────────
pycryptodome==3.23.0

# ── Date utilities ────────────────────────────────────────────
python-dateutil==2.9.0.post0
six==1.17.0

# ── Async / timeout ───────────────────────────────────────────
async-timeout==5.0.1

# ── C extensions (auto deps) ──────────────────────────────────
cffi==2.0.0
pycparser==3.0

# ── Your custom app ───────────────────────────────────────────
scheduler_app==0.1.0

# ── Typing / extensions ───────────────────────────────────────
typing_extensions==4.15.0

# ── Timezone local detection ──────────────────────────────────
tzlocal==5.3.1

# ── File watch (dev server) ───────────────────────────────────
watchdog==6.0.0

# ── Misc ──────────────────────────────────────────────────────
timedelta==2020.12.3
et_xmlfile==2.0.0


Total packages
14
22