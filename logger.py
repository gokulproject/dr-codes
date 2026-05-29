if not already_ran and start_at_raw is not None:
                if start_at_raw >= now_utc:
                    fire_utc = start_at_raw
                    mode = "start_at (FIRST)"
                else:
                    # start_at already passed — find next slot
                    # anchored from start_at so schedule stays on pattern
                    # e.g. start_at=7:00, now=7:10, interval=1hr → 8:00
                    _interval = _cron_to_timedelta(s["cron_expression"])
                    candidate = start_at_raw
                    while candidate <= now_utc:
                        candidate += _interval
                    fire_utc = candidate
                    mode = "start_at PAST -> next slot"
                run_num = 1