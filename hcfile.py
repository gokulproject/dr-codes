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