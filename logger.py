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