# ==============================================================================
# LOGGING
# Directory layout:
#   logs/
#     app/
#       healthcheck.log        — healthcheck scheduler, executor, views
#       navitas_account.log    — platform requests, signals
#       scheduler_app.log      — scheduler_app tasks
#       easyaudit.log          — audit trail
#     django/
#       django.log             — Django core only (INFO+)
#       requests.log           — HTTP request/response
#       security.log           — django.security events
#     critical/
#       critical.log           — ERROR + CRITICAL from every source
# ==============================================================================

LOG_BASE = BASE_DIR / 'logs'

_LOG_DIRS = {
    'app':      LOG_BASE / 'app',
    'django':   LOG_BASE / 'django',
    'critical': LOG_BASE / 'critical',
}

for _d in _LOG_DIRS.values():
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        pass


def _rotating(path, level='DEBUG', fmt='verbose', max_mb=10, backups=10):
    return {
        'class':       'logging.handlers.RotatingFileHandler',
        'filename':    str(path),
        'maxBytes':    max_mb * 1024 * 1024,
        'backupCount': backups,
        'formatter':   fmt,
        'encoding':    'utf-8',
        'level':       level,
        'delay':       False,
    }


# Paths used in filters
import re as _re

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format':  '[{asctime}] {levelname:<8} {name:<40} pid={process} | {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style':   '{',
        },
        'simple': {
            'format':  '[{asctime}] {levelname:<8} | {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style':   '{',
        },
        'request_fmt': {
            'format':  '[{asctime}] {levelname:<8} {name} | {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style':   '{',
        },
    },

    # --------------------------------------------------------------------------
    # Filters
    # --------------------------------------------------------------------------
    'filters': {
        # Suppress noisy healthcheck DEBUG lines from qcluster workers
        # Removes: "Skipping APScheduler (qcluster process - not needed here)"
        'ignore_qcluster_skip': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda r: not (
                r.name == 'healthcheck.apps'
                and r.levelno == 10          # DEBUG only
                and 'Skipping APScheduler' in r.getMessage()
            ),
        },
        # Suppress /api/db-health/ polling spam from navitas_account at DEBUG
        'ignore_dbhealth_debug': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda r: not (
                r.levelno == 10              # DEBUG only
                and 'db-health' in r.getMessage()
            ),
        },
        # Suppress apscheduler internal chatter (Adding job tentatively, etc.)
        'ignore_apscheduler_verbose': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda r: not (
                r.name.startswith('apscheduler')
                and r.levelno < 30           # below WARNING
                and any(phrase in r.getMessage() for phrase in [
                    'Adding job tentatively',
                    'Running job',
                    'executed successfully',
                    'Job store',
                ])
            ),
        },
    },

    # --------------------------------------------------------------------------
    # Handlers
    # --------------------------------------------------------------------------
    'handlers': {

        # Console — dev only (Apache/mod_wsgi suppresses stdout)
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'verbose',
            'level':     'DEBUG',
        },

        # ── App log files ──────────────────────────────────────────────────────
        'file_healthcheck': {
            **_rotating(_LOG_DIRS['app'] / 'healthcheck.log', max_mb=20, backups=15),
            'filters': ['ignore_qcluster_skip', 'ignore_apscheduler_verbose'],
        },

        'file_navitas': {
            **_rotating(_LOG_DIRS['app'] / 'navitas_account.log'),
            'filters': ['ignore_dbhealth_debug'],
        },

        'file_scheduler_app': _rotating(_LOG_DIRS['app'] / 'scheduler_app.log'),

        'file_easyaudit': _rotating(
            _LOG_DIRS['app'] / 'easyaudit.log', level='INFO', max_mb=5
        ),

        # ── Django core files ──────────────────────────────────────────────────
        'file_django': _rotating(_LOG_DIRS['django'] / 'django.log', level='INFO'),

        'file_requests': _rotating(
            _LOG_DIRS['django'] / 'requests.log',
            fmt='request_fmt', max_mb=20, backups=15
        ),

        'file_security': _rotating(_LOG_DIRS['django'] / 'security.log', max_mb=5),

        # ── Critical — ERROR + CRITICAL from every source ──────────────────────
        # FIX: RotatingFileHandler works on Windows; WatchedFileHandler did not.
        'file_critical': _rotating(
            _LOG_DIRS['critical'] / 'critical.log',
            level='ERROR',
            fmt='verbose',
            max_mb=20,
            backups=20,
        ),

    },  # ← CLOSE handlers

    # --------------------------------------------------------------------------
    # Root — catches anything not matched by a named logger
    # FIX: root now includes file_critical so no ERROR ever goes unrecorded
    # --------------------------------------------------------------------------
    'root': {
        'handlers': ['console', 'file_django', 'file_critical'],
        'level':    'INFO',
    },

    # --------------------------------------------------------------------------
    # Loggers
    # --------------------------------------------------------------------------
    'loggers': {

        # ── Your apps ──────────────────────────────────────────────────────────
        'healthcheck': {
            'handlers':  ['console', 'file_healthcheck', 'file_critical'],
            'level':     'DEBUG',
            'propagate': False,
        },
        'hc_scheduler': {
            'handlers':  ['console', 'file_healthcheck', 'file_critical'],
            'level':     'INFO',   # was DEBUG — scheduler fires every minute, no need for DEBUG
            'propagate': False,
        },
        'hc': {
            'handlers':  ['console', 'file_healthcheck', 'file_critical'],
            'level':     'DEBUG',
            'propagate': False,
        },
        'scheduler_app': {
            'handlers':  ['console', 'file_scheduler_app', 'file_critical'],
            'level':     'DEBUG',
            'propagate': False,
        },
        'navitas_account': {
            'handlers':  ['console', 'file_navitas', 'file_critical'],
            'level':     'DEBUG',
            'propagate': False,
        },
        'easyaudit': {
            'handlers':  ['console', 'file_easyaudit', 'file_critical'],
            'level':     'INFO',
            'propagate': False,
        },

        # ── Django core ────────────────────────────────────────────────────────
        'django': {
            'handlers':  ['console', 'file_django', 'file_critical'],
            'level':     'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers':  ['console', 'file_requests', 'file_critical'],
            'level':     'WARNING',  # only log 4xx/5xx — removes 200 OK noise
            'propagate': False,
        },
        'django.server': {
            'handlers':  ['console', 'file_requests', 'file_critical'],  # FIX: added file_critical
            'level':     'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers':  ['console', 'file_security', 'file_critical'],
            'level':     'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers':  ['file_django', 'file_critical'],               # FIX: added file_critical
            'level':     'WARNING',
            'propagate': False,
        },
        'django.template': {
            'handlers':  ['file_django', 'file_critical'],               # FIX: added file_critical
            'level':     'INFO',
            'propagate': False,
        },

        # ── APScheduler library internals → healthcheck.log ───────────────────
        'apscheduler': {
            'handlers':  ['console', 'file_healthcheck', 'file_critical'],
            'level':     'WARNING',  # only log warnings/errors from apscheduler itself
            'propagate': False,
        },

        # ── Third-party ────────────────────────────────────────────────────────
        'py.warnings': {
            'handlers':  ['file_django', 'file_critical'],               # FIX: added file_critical
            'level':     'WARNING',
            'propagate': False,
        },
    },
}

# ==============================================================================
# OTHERS
# ==============================================================================

HC_ENC_KEY = os.environ.get('HC_ENC_KEY', 'default-32-byte-key-change-me!!')

# Project name constant used in templates
PROJECT_NAME = 'Navitas Control Center'

# ==============================================================================
# Q CLUSTER CODE AND LOGGING
# ==============================================================================

Q_CLUSTER = {
    'name':         'Navitas-Scheduler',
    'workers':      4,           # was 8 — fewer workers, each gets more resources
    'recycle':      50,          # was 500 — recycle worker after 50 tasks (prevents memory/conn leaks)
    'timeout':      240,         # task is KILLED after 240s (must be < retry)
    'retry':        300,         # task re-queued after 300s if not acked (must be > timeout)
    'max_attempts': 3,           # give up after 3 failures — stops infinite retry loops
    'ack_failures': True,        # ACK even failed tasks — removes them from queue properly
    'save_limit':   250,         # keep only last 250 successes in DB (prevents table bloat)
    'queue_limit':  50,
    'bulk':         10,
    'orm':          'default',
    'catch_up':     False,       # skip missed scheduled runs — never pile up
    'poll':         2,           # check queue every 2s (default is 0.2 — too aggressive for ORM)
}
