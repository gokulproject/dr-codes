if not already_ran and start_at_raw is not None:
    if start_at_raw >= now_utc:
        fire_utc = start_at_raw
        mode = "start_at (FIRST)"
    else:
        # OLD: fire_utc = now_utc + timedelta(seconds=5)
        # NEW: anchor from start_at → find next valid slot
        # e.g. start_at=7:00, now=7:10, interval=1hr → 8:00
        _interval = _cron_to_timedelta(s["cron_expression"])
        candidate = start_at_raw
        while candidate <= now_utc:
            candidate += _interval
        fire_utc = candidate
        mode = "start_at PAST -> next slot"
    run_num = 1




if esc_cfg:
                            _do_resolved = (esc_cfg.get("send_resolved_mail") and
                                            esc_cfg.get("env_mail_enabled", True))
                        else:
                            _do_resolved = True
                        if _do_resolved:
                            email_svc.send_resolved(
                                run_id=self.run_id,
                                customer_id=customer_id,
                                customer_name=cname,
                                env_type=env_type,
                                resolved_issues=env_resolved)



recipients = self.db.fetch_all(
            """SELECT mr.to_addresses As email_to ,mr.cc_addresses As email_cc
               FROM mail_recipients mr
               WHERE mr.customer_id=%s
                  AND mr.alert_type='RESOLVED'
                  AND mr.is_active=1""",
            (customer_id,))
        if not recipients:
            # Fallback — use default recipients (customer_id IS NULL)
            recipients = self.db.fetch_all(
                """SELECT mr.to_addresses As email_to, mr.cc_addresses As email_cc
                   FROM mail_recipients mr
                   WHERE mr.customer_id IS NULL
                     AND mr.alert_type='RESOLVED'
                     AND mr.is_active=1""")
        if not recipients:
            return





<div class="col-md-2">
            <input type="date" name="dash_date"
                   class="form-control form-control-sm"
                   value="{{ dash_date }}"
                   title="Filter by run date">
          </div>



if dash_date:
            from datetime import datetime, timedelta
            try:
                day_start = datetime.strptime(dash_date, "%Y-%m-%d")
                day_end   = day_start + timedelta(days=1)
                runs_qs   = runs_qs.filter(
                    started_at__gte=day_start,
                    started_at__lt=day_end)
            except ValueError:
                pass


href="?dash_page={{ runs_page.previous_page_number }}&dash_customer={{ dash_customer }}&dash_status={{ dash_status }}&dash_env={{ dash_env }}&dash_date={{ dash_date }}"


href="?dash_page={{ runs_page.next_page_number }}&dash_customer={{ dash_customer }}&dash_status={{ dash_status }}&dash_env={{ dash_env }}&dash_date={{ dash_date }}"



______________

"""
healthcheck/scheduler_service.py  (v10 – self-scheduling DateTrigger chain)
============================================================================
ROOT CAUSE FIX:
  CronTrigger is clock-anchored. "*/10 * * * *" fires at :00, :10, :20...
  If start_at = 4:08, CronTrigger would fire at 4:10 (2 min late), then 4:20...
  This is WRONG. User wants: 4:08 → 4:18 → 4:28 (exact interval from start_at).
 
SOLUTION — Self-scheduling DateTrigger chain:
  1. Register ONE DateTrigger at exact start_at (0s delay).
  2. When that fires and run completes → schedule NEXT DateTrigger at (last_run + interval).
  3. Repeat forever. Interval derived from cron expression.
 
RESULT:
  start_at=4:08, cron=*/10  → 4:08, 4:18, 4:28, 4:38... (exact, no clock drift)
  start_at=4:43, cron=0 */1 → 4:43, 5:43, 6:43, 7:43... (exact, preserves :43)
  start_at=9:17, cron=*/5   → 9:17, 9:22, 9:27, 9:32... (exact 5min from 9:17)
 
TIMEZONE: All inputs IST → stored UTC → displayed IST 12-hour.
"""
import logging
import threading
from datetime import datetime, timedelta, timezone as _dtz
from typing import Optional
import atexit
logger = logging.getLogger("hc.scheduler")
 
_scheduler       = None
_scheduler_lock  = threading.Lock()
_active_runs: dict = {}
_active_runs_lock  = threading.Lock()
 
# ── Timezone constants from ist_utils (reads settings.TIME_ZONE) ───────────
from healthcheck.ist_utils import (
    IST_OFFSET, IST_TZ_NAME, TZ_ABBR,
    utc_to_ist as _utc_to_ist_ref,
    ist_to_utc as _ist_to_utc_ref,
    now_ist as _now_ist_ref,
)
 
 
# ── IST / UTC helpers ──────────────────────────────────────────────────────
def _now_utc() -> datetime:
    return datetime.utcnow()
 
def _now_ist() -> datetime:
    return _now_ist_ref()
 
def _utc_to_ist(dt: datetime) -> datetime:
    return _utc_to_ist_ref(dt)
 
def _ist_to_utc(dt: datetime) -> datetime:
    return _ist_to_utc_ref(dt)
 
def _strip_tz(dt: datetime) -> Optional[datetime]:
    if dt is None: return None
    return dt.replace(tzinfo=None) if (hasattr(dt,'tzinfo') and dt.tzinfo) else dt
 
def _fmt(dt: datetime) -> str:
    if dt is None: return "Never"
    return _utc_to_ist(_strip_tz(dt)).strftime("%d-%b-%Y %I:%M %p IST")
 
 
# ── Interval extraction from cron expression ──────────────────────────────
def _cron_to_timedelta(cron_expr: str) -> timedelta:
    """
    Convert cron expression to a timedelta interval.
    Uses croniter to find the difference between first two ticks.
 
    Examples:
      "*/5 * * * *"   →  timedelta(minutes=5)
      "*/10 * * * *"  →  timedelta(minutes=10)
      "0 */1 * * *"   →  timedelta(hours=1)
      "0 0 * * *"     →  timedelta(hours=24)
      "0 0 * * 0"     →  timedelta(days=7)
      "30 9 * * *"    →  timedelta(hours=24)  ← daily at 9:30
    """
    try:
        from croniter import croniter
        base = datetime(2026, 1, 1, 0, 0, 0)
        ci = croniter(cron_expr, base)
        t1 = ci.get_next(datetime)
        t2 = ci.get_next(datetime)
        delta = t2 - t1
        if delta.total_seconds() < 60:
            logger.warning(f"Cron '{cron_expr}' interval < 60s — using 60s minimum")
            return timedelta(minutes=1)
        return delta
    except Exception as exc:
        logger.error(f"Cannot parse cron '{cron_expr}': {exc}. Defaulting to 1 hour.")
        return timedelta(hours=1)
 
 
# ── DB error types ─────────────────────────────────────────────────────────
def _db_err():
    types = (ConnectionError,)
    try:
        from healthcheck.hc_db_manager import DBConnectionError
        types += (DBConnectionError,)
    except ImportError: pass
    try:
        import pymysql.err as pe
        types += (pe.OperationalError, pe.InterfaceError)
    except ImportError: pass
    return types
 
def _get_engine():
    from healthcheck.engine_bridge import get_engine
    return get_engine()
 
 
# ── Tracker helpers ─────────────────────────────────────────────────────────
def _update_tracker(db, tid: int, **kw):
    if not kw or not tid: return
    try:
        db.execute(
            "UPDATE scheduler_tracker SET " +
            ", ".join(f"{k}=%s" for k in kw) +
            ", updated_at=NOW() WHERE id=%s",
            list(kw.values()) + [tid])
    except Exception as e:
        logger.warning(f"tracker update: {e}")
 
def _create_tracker(db, schedule_id, customer_id, env_types,
                    schedule_name, cron_expr, fire_utc,
                    triggered_by="apscheduler") -> int:
    try:
        return db.insert_get_id(
            """INSERT INTO scheduler_tracker
               (schedule_id,customer_id,env_types,schedule_name,cron_expression,
                status,scheduled_fire_at,triggered_by,is_active,created_at,updated_at)
               VALUES(%s,%s,%s,%s,%s,'PENDING',%s,%s,1,NOW(),NOW())""",
            (schedule_id,customer_id,env_types,schedule_name,
             cron_expr,fire_utc,triggered_by))
    except Exception as e:
        logger.warning(f"tracker insert: {e}"); return 0
 
 
# ── Core execution ─────────────────────────────────────────────────────────
def _execute_run(run_id: int, label: str, tracker_id: int = 0):
    """Execute a HC run in its own thread. COM-safe."""
    _ci = False
    try: import pythoncom; pythoncom.CoInitialize(); _ci = True
    except Exception: pass
 
    eng = _get_engine()
    with _active_runs_lock: _active_runs[run_id] = label
    try:
        with eng["DBManager"]() as db:
            eng["ConfigLoader"].load(db)
            if tracker_id:
                _update_tracker(db, tracker_id, run_id=run_id,
                                status="RUNNING", actual_start_at=_now_utc())
            eng["RunLauncher"](db, run_id, eng["ConfigLoader"].get()).launch()
        final = _get_status(run_id)
        logger.info(f"[Sched] Run #{run_id} ({label}) → {final}")
        if tracker_id:
            with eng["DBManager"]() as db:
                st = "COMPLETED" if final in ("COMPLETED","PARTIAL") else "FAILED"
                _update_tracker(db, tracker_id, status=st,
                                completed_at=_now_utc(),
                                error_message=None if st=="COMPLETED" else final)
    except Exception as exc:
        logger.error(f"[Sched] Run #{run_id} error: {exc}", exc_info=True)
        if tracker_id:
            try:
                with eng["DBManager"]() as db:
                    _update_tracker(db, tracker_id, status="FAILED",
                                    completed_at=_now_utc(), error_message=str(exc)[:1000])
            except Exception: pass
    finally:
        with _active_runs_lock: _active_runs.pop(run_id, None)
        if _ci:
            try: import pythoncom; pythoncom.CoUninitialize()
            except Exception: pass
 
def _get_status(run_id: int) -> str:
    try:
        with _get_engine()["DBManager"]() as db:
            r = db.fetch_one("SELECT status FROM execution_runs WHERE id=%s",(run_id,))
            return r["status"] if r else "UNKNOWN"
    except Exception: return "UNKNOWN"
 
 
# ── RERUN QUEUE PROCESSOR ─────────────────────────────────────────────────
def _process_rerun_queue():
    """
    Poll rerun_queue for PENDING entries whose scheduled_at has passed,
    and execute each one in its own background thread.
 
    Scheduled as an APScheduler interval job (every 60 s) so reruns fire
    at the correct time without relying on the old blocking poll loop.
    """
    eng = _get_engine()
    try:
        with eng["DBManager"]() as db:
            eng["ConfigLoader"].load(db)
            pending = db.fetch_all(
                """SELECT rq.*, c.name AS cname
                   FROM rerun_queue rq
                   JOIN customers c ON c.id=rq.customer_id
                   WHERE rq.status='PENDING' AND rq.scheduled_at<=NOW()
                   ORDER BY rq.scheduled_at""")
    except Exception as exc:
        logger.error(f"[Rerun] Cannot fetch rerun_queue: {exc}")
        return
 
    if not pending:
        return
 
    logger.info(f"[Rerun] Processing {len(pending)} pending rerun(s)")
 
    for entry in pending:
        _fire_rerun_entry(entry)
 
 
def _fire_rerun_entry(entry: dict):
    """Execute one rerun_queue entry in a background thread."""
    entry_id    = entry["id"]
    cname       = entry.get("cname", str(entry["customer_id"]))
    env_types   = entry["env_types"]
    label       = f"{cname}/{env_types}"
 
    def _do_rerun():
        _ci = False
        try:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                _ci = True
            except Exception:
                pass
 
            eng = _get_engine()
            run_id = 0
            try:
                with eng["DBManager"]() as db:
                    eng["ConfigLoader"].load(db)
 
                    # Claim the entry atomically
                    affected = db.execute(
                        "UPDATE rerun_queue SET status='IN_PROGRESS', started_at=NOW() "
                        "WHERE id=%s AND status='PENDING'",
                        (entry_id,))
                    if not affected:
                        # Another thread/process already claimed it
                        return
 
                    run_id = db.insert_get_id(
                        """INSERT INTO execution_runs
                           (customer_id, env_types, run_type, status,
                            triggered_by, rerun_of_run_id, rerun_attempt)
                           VALUES (%s,%s,'RERUN','PENDING','apscheduler_rerun',%s,%s)""",
                        (entry["customer_id"], env_types,
                         entry["original_run_id"], entry["attempt_number"]))
 
                logger.info(
                    f"[Rerun] {label} | attempt {entry['attempt_number']}/{entry['max_attempts']}"
                    f" → Run #{run_id}")
 
                # Execute the run.
                # run_launcher._queue_rerun() (called inside _execute_run)
                # handles all post-run queue management for FAILED/PARTIAL:
                #   • closes THIS row  (FAILED / EXHAUSTED)
                #   • inserts the next PENDING attempt if retries remain
                #   • sends the exhausted notification email
                #
                # EXCEPTION: run_launcher SKIPS _queue_rerun entirely when
                # final_status == "COMPLETED" (see run_launcher.py step 6:
                #   if final_status in ("FAILED","PARTIAL"): _queue_rerun()
                #   else: SKIPPED
                # ).  So for COMPLETED we MUST close the row here ourselves.
                # This is the fix for the "stuck IN_PROGRESS after success" bug.
                _execute_run(run_id, label)
 
                final_status = _get_status(run_id)
                if final_status == "COMPLETED":
                    # run_launcher did NOT call _queue_rerun — close the row now
                    with eng["DBManager"]() as db:
                        db.execute(
                            "UPDATE rerun_queue SET status='COMPLETED', completed_at=NOW() "
                            "WHERE id=%s",
                            (entry_id,))
                    logger.info(f"[Rerun] {label} | Run #{run_id} COMPLETED ✓ — queue row closed")
                else:
                    # FAILED / PARTIAL / other: run_launcher._queue_rerun
                    # already closed the row and queued next attempt if needed.
                    logger.info(
                        f"[Rerun] {label} | Run #{run_id} status={final_status} "
                        f"(attempt {entry['attempt_number']}/{entry['max_attempts']}) "
                        f"— row managed by run_launcher")
 
            except Exception as exc:
                logger.error(f"[Rerun] entry {entry_id} error: {exc}", exc_info=True)
                try:
                    with eng["DBManager"]() as db:
                        db.execute(
                            "UPDATE rerun_queue SET status='FAILED', "
                            "last_error=%s WHERE id=%s",
                            (str(exc)[:1000], entry_id))
                except Exception:
                    pass
 
        finally:
            if _ci:
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
 
    t = threading.Thread(
        target=_do_rerun,
        daemon=True,
        name=f"hc_rerun_{entry_id}")
    t.start()
 
 
# ── THE CHAIN RUNNER ───────────────────────────────────────────────────────
def _chain_run(schedule_id: int, customer_id: int, env_types: str,
               schedule_name: str, customer_name: str,
               cron_expression: str, run_number: int = 1):
    """
    Execute one run, then immediately schedule the NEXT DateTrigger.
 
    Chain: start_at DateTrigger → _chain_run(1)
              → executes run
              → schedules DateTrigger(last_run + interval) → _chain_run(2)
              → executes run
              → schedules DateTrigger(last_run + interval) → _chain_run(3)
              → ...
 
    This means the exact minute from start_at is preserved forever.
    """
    global _scheduler
 
    label   = f"{customer_name}/{env_types}"
    now_utc = _now_utc()
    now_ist = _utc_to_ist(now_utc)
 
    logger.info(
        f"[Sched] RUN #{run_number} '{schedule_name}' | {label} | "
        f"IST={now_ist.strftime('%d-%b-%Y %I:%M:%S %p')}")
 
    # ── Compute next run time ─────────────────────────────────────
    # OLD CODE (commented) — used fixed interval offset, could drift
    # and gave wrong next_run_at for weekly/non-daily crons:
    #   interval = _cron_to_timedelta(cron_expression)
    #   next_ist = now_ist + interval   # e.g. Wed 9AM + 7days = Wed → wrong for Mon cron
    #   next_utc = _ist_to_utc(next_ist)
    #
    # NEW CODE — uses croniter to find exact next cron tick after this run.
    # Example: cron=0 6 * * 1 (Monday 6AM), run completes Monday 6:01AM
    #   croniter.get_next() → next Monday 6:00 AM  ✅ always correct
    from croniter import croniter as _ci
    _cron    = _ci(cron_expression, now_ist)
    next_ist = _cron.get_next(datetime)
    next_utc = next_ist - timedelta(hours=5, minutes=30)
    interval = _cron_to_timedelta(cron_expression)   # kept for log display only
 
    eng = _get_engine()
    tracker_id = 0
    run_id     = 0
 
    try:
        # ── Step 1: READ-ONLY check — short connection, no write lock ────────
        # Load config and check is_active in a separate read-only connection
        # that is closed before any write begins. This prevents a long-lived
        # connection from accumulating an open transaction while we later write
        # to `schedules`, which would compete with Django admin saves.
        with eng["DBManager"]() as db:
            eng["ConfigLoader"].load(db)
            sch = db.fetch_one(
                "SELECT is_active FROM schedules WHERE id=%s", (schedule_id,))
        if not sch or not sch["is_active"]:
            logger.info(
                f"[Sched] '{schedule_name}' deactivated — stopping chain.")
            return
 
        # ── Step 2: INSERT tracker + run — separate short connection ─────────
        # Keep this separate from the schedules UPDATE so each write
        # acquires and releases its lock independently. A single long-lived
        # connection holding locks on scheduler_tracker + execution_runs +
        # schedules simultaneously widens the lock window and increases
        # the probability of a 1205 collision with admin saves.
        with eng["DBManager"]() as db:
            tracker_id = _create_tracker(
                db, schedule_id, customer_id, env_types,
                schedule_name, cron_expression, now_utc)
 
            run_id = db.insert_get_id(
                """INSERT INTO execution_runs
                   (schedule_id,customer_id,env_types,
                    run_type,status,triggered_by)
                   VALUES(%s,%s,%s,'SCHEDULED','PENDING','apscheduler')""",
                (schedule_id, customer_id, env_types))
 
        # ── Step 3: UPDATE schedules — shortest possible lock window ─────────
        # This is the row that admin saves also UPDATE. By using a dedicated
        # connection that opens, executes one UPDATE, commits, and closes, the
        # InnoDB row-lock on `schedules` is held for the minimum possible time.
        with eng["DBManager"]() as db:
            db.execute(
                "UPDATE schedules SET last_run_at=%s, next_run_at=%s WHERE id=%s",
                (now_utc, next_utc, schedule_id))
 
        # ── Step 4: UPDATE tracker with run_id + timestamps ──────────────────
        if tracker_id:
            with eng["DBManager"]() as db:
                _update_tracker(db, tracker_id,
                                run_id=run_id,
                                last_run_at=now_utc,
                                next_run_at=next_utc)
 
        logger.info(
            f"[Sched] Run #{run_id} created | "
            f"last={now_ist.strftime(f'%I:%M %p {TZ_ABBR}')} | "
            f"next={next_ist.strftime(f'%I:%M %p {TZ_ABBR}')} "
            f"(+{int(interval.total_seconds()//60)}min)")
 
        # ── Schedule NEXT run BEFORE executing this one ─────────────────
        # This ensures next run is queued even if this run crashes
        _schedule_next(schedule_id, customer_id, env_types,
                       schedule_name, customer_name,
                       cron_expression, next_utc, run_number + 1)
 
        # ── Execute this run ─────────────────────────────────────────────
        _execute_run(run_id, label, tracker_id)
 
    except Exception as exc:
        if isinstance(exc, _db_err()):
            logger.error(
                f"[Sched] DB down for '{schedule_name}'. "
                f"Rescheduling next in {int(interval.total_seconds()//60)}min.")
            # Still schedule next even when DB is down
            _schedule_next(schedule_id, customer_id, env_types,
                           schedule_name, customer_name,
                           cron_expression, next_utc, run_number + 1)
            return
        logger.error(f"[Sched] chain_run error '{schedule_name}': {exc}", exc_info=True)
        if tracker_id:
            try:
                with eng["DBManager"]() as db:
                    _update_tracker(db, tracker_id, status="FAILED",
                                    error_message=str(exc)[:1000])
            except Exception: pass
 
 
def _schedule_next(schedule_id: int, customer_id: int, env_types: str,
                   schedule_name: str, customer_name: str,
                   cron_expression: str, fire_at_utc: datetime,
                   run_number: int):
    """
    Register a DateTrigger for the next run.
    fire_at_utc is already computed as (last_run_utc + interval).
    """
    global _scheduler
    if _scheduler is None or not _scheduler.running:
        logger.warning(f"[Sched] Scheduler stopped — cannot schedule next for '{schedule_name}'")
        return
 
    from apscheduler.triggers.date import DateTrigger
 
    job_id   = f"sched_{schedule_id}"
    fire_ist = _utc_to_ist(fire_at_utc)
 
    try:
        # Convert UTC → aware datetime for APScheduler
        fire_aware = fire_at_utc.replace(tzinfo=_dtz.utc)
        trigger    = DateTrigger(run_date=fire_aware, timezone=IST_TZ_NAME)
 
        _scheduler.add_job(
            _chain_run,
            trigger=trigger,
            id=job_id,
            name=schedule_name,
            args=[schedule_id, customer_id, env_types,
                  schedule_name, customer_name, cron_expression, run_number],
            max_instances=1,
            replace_existing=True)
 
        logger.info(
            f"[Sched] Next DateTrigger: run #{run_number} "
            f"'{schedule_name}' @ {fire_ist.strftime(f'%d-%b-%Y %I:%M %p {TZ_ABBR}')}")
    except Exception as exc:
        logger.error(f"[Sched] Failed to schedule next for '{schedule_nam