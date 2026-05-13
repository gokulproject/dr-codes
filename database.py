return HealthCheckConfigData(
    excel_output_path=s(
        "excel_output_path",
        r"C:\cloudFTP\Health-Check-OUT\Excel"
    ),

    log_output_path=s(
        "log_output_path",
        r"C:\cloudFTP\Health-Check-OUT\Log"
    ),

    oracle_dll_path=s(
        "oracle_dll_path",
        ""
    ),

    excel_title_prefix=s(
        "excel_title_prefix",
        "Health Check Report"
    ),

    conn_retry_attempts=i(
        "conn_retry_attempts",
        3
    ),

    conn_retry_delay_sec=i(
        "conn_retry_delay_sec",
        10
    ),

    disk_free_threshold_gb=f(
        "disk_free_threshold_gb",
        10.0
    ),

    tablespace_free_pct=f(
        "tablespace_free_pct",
        25.0
    ),

    # 0.083 ~= 5 minutes
    rerun_interval_hours=f(
        "rerun_interval_hours",
        24.0
    ),

    rerun_max_attempts=i(
        "rerun_max_attempts",
        3
    ),

    log_retention_days=i(
        "log_retention_days",
        90
    ),

    timezone=s(
        "timezone",
        IST_TZ_NAME
    ),

    stuck_run_timeout_minutes=i(
        "stuck_run_timeout_minutes",
        90
    ),

    mail=mail_cfg,

    templates=templates,
)
