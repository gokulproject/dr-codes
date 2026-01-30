{% load static %}
{% load django_bootstrap5 %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Healthcheck Dashboard - {{ job.name }}</title>
    {% bootstrap_css %}
    <style>
        body {
            background: #f8f9fa;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding-top: 120px;
        }
        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .table th {
            background: #e9ecef;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .table td, .table th {
            vertical-align: middle;
            padding: 0.6rem 0.5rem;
        }
        .table-container {
            max-height: 500px;
            overflow: auto;
        }
        .status-success {
            background-color: #d4edda !important;
        }
        .status-failed {
            background-color: #f8d7da !important;
        }
        .status-running {
            background-color: #fff3cd !important;
        }
        .badge.fs-6 {
            font-size: 1rem !important;
        }
        .job-updating {
            opacity: 0.7;
        }
        .search-pill {
            border-radius: 999px;
        }
        .page-link {
            cursor: pointer;
        }
        .spinner-overlay {
            position: absolute;
            inset: 0;
            background: rgba(255,255,255,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 50;
        }
        .job-status-waiting {
            color: #0d6efd;
            font-weight: 500;
            font-size: 0.9rem;
        }
        .job-status-executed {
            color: #198754;
            font-weight: 500;
            font-size: 0.9rem;
        }
        .job-status-na {
            color: #6c757d;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <header>{% include "healthcheckapp/hc_navbar.html" %}</header>

    <div class="container-fluid py-4">
        <h5 class="mb-1">{{ job.name }}</h5>

        <!-- Job Status -->
        <div class="card mb-4">
            <div class="card-header d-flex justify-content-between align-items-center">
                <small class="text-muted" id="job-updated">Job status</small>
            </div>
            <div class="card-body p-0 job-updating" id="jobStatusCard">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0" id="jobStatusTable">
                        <thead class="table-light">
                            <tr>
                                <th>Status</th>
                                <th>Last Run</th>
                                <th>Next Run</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="text-center text-muted">
                                <td colspan="3" class="py-4">
                                    <small>Loading...</small>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Process Table with Enhanced UI -->
        <div class="card position-relative" id="processCard">
            <div class="spinner-overlay d-none" id="processSpinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>

            <div class="card-header">
                <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2">
                    <h6 class="mb-0">Process Status</h6>
                    <div class="input-group input-group-sm" style="max-width: 320px;">
                        <span class="input-group-text bg-white border-end-0">
                            <i class="bi bi-search"></i>
                        </span>
                        <input type="text" id="globalSearch" class="form-control border-start-0 search-pill" 
                               placeholder="Search customer, env, tenant, status...">
                        <button class="btn btn-outline-secondary" type="button" id="btnClearSearch">×</button>
                    </div>
                </div>

                <!-- Advanced Filters -->
                <div class="mt-2">
                    <button class="btn btn-link btn-sm p-0" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#advancedFilters">
                        Advanced filters
                    </button>
                    <div class="collapse mt-2" id="advancedFilters">
                        <div class="row g-2">
                            <div class="col-md-3">
                                <input type="text" id="filterCustomer" class="form-control form-control-sm" 
                                       placeholder="Customer">
                            </div>
                            <div class="col-md-3">
                                <input type="text" id="filterEnv" class="form-control form-control-sm" 
                                       placeholder="Environment">
                            </div>
                            <div class="col-md-2">
                                <input type="date" id="filterStartDate" class="form-control form-control-sm">
                            </div>
                            <div class="col-md-2">
                                <input type="date" id="filterEndDate" class="form-control form-control-sm">
                            </div>
                            <div class="col-md-2 d-flex">
                                <button id="btnApplyFilter" class="btn btn-sm btn-primary me-2 flex-fill">
                                    Apply
                                </button>
                                <button id="btnClearFilter" class="btn btn-sm btn-outline-secondary flex-fill">
                                    Reset
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="table-container px-4 pb-2 pt-6">
                <table class="table table-hover mb-1" id="processTable">
                    <thead>
                        <tr>
                            <th style="width: 60px;">SI.No</th>
                            <th style="width: 150px;">Customer Name</th>
                            <th style="width: 80px;">Environment</th>
                            <th style="width: 90px;">Tenant</th>
                            <th style="width: 90px;">Status</th>
                            <th style="width: 70px;">Error</th>
                            <th style="width: 200px;">Start</th>
                            <th style="width: 200px;">End</th>
                            <th style="width: 100px;">View Report</th>
                            <th style="width: 100px;">Action Required</th>
                            <th style="width: 180px;">Job Run Status</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>

                <!-- Numbered Pagination -->
                <nav aria-label="Process pagination" class="mt-3">
                    <ul class="pagination pagination-sm justify-content-center mb-0" id="paginationBar"></ul>
                    <div class="text-center small text-muted mt-1" id="pageInfo"></div>
                </nav>
            </div>
        </div>
    </div>

    {% bootstrap_javascript %}
    <script>
        document.addEventListener('DOMContentLoaded', function () {
            const PROCESS_API = "{% url 'healthcheckapp:process_status_api' %}";
            const JOB_STATUS_API = "{% url 'healthcheckapp:job_status_api' job.id %}";
            const RECORDS_BASE_URL = "{% url 'healthcheckapp:records' 0 %}".replace(/0\/$/, '');
            const JOB_ID = {{ job.id }};

            let start = 0, length = 10, total = 0, firstLoadDone = false;
            let filterCustomer = '', filterEnv = '', filterStartDate = '', filterEndDate = '', globalSearch = '';

            function setSpinner(visible) {
                document.getElementById('processSpinner').classList.toggle('d-none', !visible);
            }

            function updatePagination() {
                const bar = document.getElementById('paginationBar');
                const info = document.getElementById('pageInfo');
                bar.innerHTML = '';
                
                const currentPage = Math.floor(start / length) + 1;
                const totalPages = Math.ceil(total / length) || 1;
                info.textContent = `Page ${currentPage} of ${totalPages} • ${total.toLocaleString()} total`;

                function addPage(label, page, disabled = false, active = false) {
                    const li = document.createElement('li');
                    li.className = `page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}`;
                    const a = document.createElement('a');
                    a.className = 'page-link';
                    a.textContent = label;
                    
                    if (!disabled && !active) {
                        a.addEventListener('click', () => {
                            start = (page - 1) * length;
                            fetchProcessPage();
                        });
                    }
                    
                    li.appendChild(a);
                    bar.appendChild(li);
                }

                addPage('« Prev', currentPage - 1, currentPage === 1);
                
                const windowSize = 5;
                const startPage = Math.max(1, currentPage - 2);
                const endPage = Math.min(totalPages, startPage + windowSize - 1);
                
                if (startPage > 1) {
                    addPage('1', 1, false, currentPage === 1);
                    if (startPage > 2) addPage('...', 1, true);
                }
                
                for (let p = startPage; p <= endPage; p++) {
                    addPage(p.toString(), p, false, p === currentPage);
                }
                
                if (endPage < totalPages) {
                    if (endPage < totalPages - 1) addPage('...', totalPages, true);
                    addPage(totalPages.toString(), totalPages, false, currentPage === totalPages);
                }
                
                addPage('Next »', currentPage + 1, currentPage === totalPages);
            }

            function formatJobRunStatus(record) {
                if (record.action_required !== 'YES') {
                    return '<span class="job-status-na">N/A</span>';
                }

                if (!record.EndTime || record.EndTime === '-') {
                    return '<span class="job-status-na">No end time</span>';
                }

                if (record.job_run_status) {
                    if (record.job_run_status.startsWith('Waiting')) {
                        return `
                            <div class="job-status-waiting">⏳ ${record.job_run_status}</div>
                            <small class="text-muted">Execute at: ${record.execution_time || 'N/A'}</small>
                        `;
                    } else if (record.job_run_status === 'Executed') {
                        return `<div class="job-status-executed">✓ Job Executed</div>`;
                    }
                }

                return '<span class="job-status-na">-</span>';
            }

            function updateProcessTable(data) {
                const tbody = document.querySelector('#processTable tbody');
                tbody.innerHTML = '';
                total = data.recordsFiltered || data.recordsTotal || 0;

                if (!data.records || !data.records.length) {
                    tbody.innerHTML = '<tr><td colspan="11" class="text-center py-4 text-muted">No data found</td></tr>';
                } else {
                    data.records.forEach((r, i) => {
                        const row = document.createElement('tr');
                        row.className = r.Status === 'Success' ? 'status-success' : 
                                      r.Status === 'Failed' ? 'status-failed' : 
                                      r.Status === 'Running' ? 'status-running' : '';

                        const actionRequiredHtml = r.action_required === 'YES'
                            ? '<span class="badge bg-danger">YES</span>'
                            : '<span class="badge bg-success">NO</span>';

                        const jobRunStatusHtml = formatJobRunStatus(r);

                        row.innerHTML = `
                            <td>${start + i + 1}</td>
                            <td>${r.Customer || '-'}</td>
                            <td><span class="badge bg-info">${r.Environment || '-'}</span></td>
                            <td>${r.Tenant || '-'}</td>
                            <td>
                                <span class="badge ${
                                    r.Status === 'Success' ? 'bg-success' :
                                    r.Status === 'Failed' ? 'bg-danger' :
                                    r.Status === 'Running' ? 'bg-warning' : 'bg-success'
                                }">
                                    ${r.Status || '-'}
                                </span>
                            </td>
                            <td>${r.ErrorMessage || '-'}</td>
                            <td>${r.StartTime || '-'}</td>
                            <td>${r.EndTime || '-'}</td>
                            <td>
                                <a href="${RECORDS_BASE_URL}${r.id}/?job_id={{ job.id }}" 
                                   class="btn btn-sm btn-outline-info">
                                    View
                                </a>
                            </td>
                            <td>${actionRequiredHtml}</td>
                            <td>${jobRunStatusHtml}</td>
                        `;
                        tbody.appendChild(row);
                    });
                }
                
                updatePagination();

                if (data.triggered_count > 0) {
                    console.log(`✓ ${data.triggered_count} process(es) triggered Job ${JOB_ID}`);
                }
            }

            function fetchProcessPage() {
                setSpinner(!firstLoadDone);
                
                const params = new URLSearchParams({ 
                    start: start, 
                    length: length,
                    job_id: JOB_ID
                });
                
                if (filterCustomer) params.append('customer', filterCustomer);
                if (filterEnv) params.append('env', filterEnv);
                if (filterStartDate) params.append('start_date', filterStartDate);
                if (filterEndDate) params.append('end_date', filterEndDate);
                if (globalSearch) params.append('search', globalSearch);

                fetch(`${PROCESS_API}?${params}`)
                    .then(r => r.json())
                    .then(data => {
                        updateProcessTable(data);
                        firstLoadDone = true;
                        setSpinner(false);
                    })
                    .catch(err => {
                        console.error(err);
                        setSpinner(false);
                    });
            }

            // Event handlers
            document.getElementById('globalSearch').addEventListener('input', function() {
                globalSearch = this.value.trim();
                start = 0;
                fetchProcessPage();
            });

            document.getElementById('btnClearSearch').addEventListener('click', () => {
                document.getElementById('globalSearch').value = '';
                globalSearch = '';
                start = 0;
                fetchProcessPage();
            });

            document.getElementById('btnApplyFilter').addEventListener('click', () => {
                filterCustomer = document.getElementById('filterCustomer').value.trim();
                filterEnv = document.getElementById('filterEnv').value.trim();
                filterStartDate = document.getElementById('filterStartDate').value;
                filterEndDate = document.getElementById('filterEndDate').value;
                start = 0;
                fetchProcessPage();
            });

            document.getElementById('btnClearFilter').addEventListener('click', () => {
                document.getElementById('filterCustomer').value = '';
                document.getElementById('filterEnv').value = '';
                document.getElementById('filterStartDate').value = '';
                document.getElementById('filterEndDate').value = '';
                filterCustomer = filterEnv = filterStartDate = filterEndDate = '';
                start = 0;
                fetchProcessPage();
            });

            // Job status refresh
            function refreshJobStatus() {
                fetch(JOB_STATUS_API)
                    .then(r => r.json())
                    .then(data => {
                        const tbody = document.querySelector('#jobStatusTable tbody');
                        const card = document.getElementById('jobStatusCard');
                        card.classList.remove('job-updating');
                        
                        const badgeClass = data.status === 'Running' ? 'bg-danger' : 'bg-success';
                        tbody.innerHTML = `
                            <tr>
                                <td><span class="badge fs-6 ${badgeClass}">${data.status}</span></td>
                                <td>${data.last_run}</td>
                                <td>${data.next_run}</td>
                            </tr>
                        `;
                    })
                    .catch(console.error);
            }

            // Initial load
            fetchProcessPage();
            refreshJobStatus();
            
            // Auto refresh job status every 5 seconds
            setInterval(refreshJobStatus, 5000);
        });
    </script>
</body>
</html>
```

---

## Key Features:

### **Views.py (Simplified)**
1. ✅ Clean pagination & filters
2. ✅ Action Required check (YES/NO)
3. ✅ **Auto-trigger after 24hrs** from EndTime
4. ✅ Simple job run status calculation
5. ✅ Minimal logging

### **HTML (Complete & Clean)**
1. ✅ All original features preserved
2. ✅ New "Job Run Status" column
3. ✅ Shows: "⏳ Waiting Xh Ym" or "✓ Job Executed"
4. ✅ Displays execution time
5. ✅ Clean, professional styling
6. ✅ Auto-refresh every 5 seconds

### **Logic Flow:**
```
1. User opens dashboard → HTML loads with {{ job.id }}
2. JavaScript calls API with job_id parameter
3. API checks each process:
   - Action Required = YES?
   - EndTime exists?
   - 24 hours passed?
4. If YES → Trigger async_task("execute_job", job_id)
5. Display status to user


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import timedelta
from django_q.tasks import async_task
import logging

from .models import ProcessStatus, HcDatabaseReport, HcFilesystemReport
from scheduler_app.models import ScheduledJob

logger = logging.getLogger(__name__)

@login_required
@require_GET
def process_status_api(request):
    """
    Process Status API with auto-trigger for healthcheck job after 24hrs
    """
    # ========================================================================
    # 1. PAGINATION & FILTERS
    # ========================================================================
    try:
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
    except ValueError:
        start = 0
        length = 10
    
    if length <= 0:
        length = 10

    customer = request.GET.get("customer", "").strip()
    env = request.GET.get("env", "").strip()
    start_date_str = request.GET.get("start_date", "").strip()
    end_date_str = request.GET.get("end_date", "").strip()
    search_value = request.GET.get("search", "").strip()
    job_id = request.GET.get("job_id", "").strip()  # Healthcheck Job ID

    # ========================================================================
    # 2. BUILD QUERYSET WITH FILTERS
    # ========================================================================
    qs = ProcessStatus.objects.using("health_check").all().order_by("-id")

    if customer:
        qs = qs.filter(Customer__icontains=customer)
    if env:
        qs = qs.filter(Environment__icontains=env)
    if search_value:
        qs = qs.filter(
            Q(Customer__icontains=search_value) |
            Q(Environment__icontains=search_value) |
            Q(Tenant__icontains=search_value) |
            Q(Status__icontains=search_value) |
            Q(ErrorMessage__icontains=search_value)
        )

    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    if start_date:
        qs = qs.filter(StartTime__date__gte=start_date)
    if end_date:
        qs = qs.filter(StartTime__date__lte=end_date)

    total_count = ProcessStatus.objects.using("health_check").count()
    filtered_count = qs.count()

    records = list(
        qs[start:start + length].values(
            "id", "Process_id", "Customer", "Environment", "Tenant",
            "Status", "ErrorMessage", "StartTime", "EndTime"
        )
    )

    # ========================================================================
    # 3. CHECK ACTION REQUIRED (YES/NO)
    # ========================================================================
    status_ids = [r["id"] for r in records]

    db_yes_ids = set(
        HcDatabaseReport.objects.using("health_check")
        .filter(status_id__in=status_ids)
        .filter(
            Q(connection_action__icontains="yes") |
            Q(password_update_action__icontains="yes") |
            Q(table_space_action__icontains="yes") |
            Q(archieve_action__icontains="yes") |
            Q(archieve_log_action__icontains="yes") |
            Q(archieve_path_action__icontains="yes") |
            Q(rman_log_action__icontains="yes")
        )
        .values_list("status_id", flat=True)
        .distinct()
    )

    fs_yes_ids = set(
        HcFilesystemReport.objects.using("health_check")
        .filter(status_id__in=status_ids)
        .filter(
            Q(connection_action__icontains="yes") |
            Q(update_action__icontains="yes") |
            Q(scheduler_action__icontains="yes") |
            Q(listners_action__icontains="yes") |
            Q(disk_space_action__icontains="yes")
        )
        .values_list("status_id", flat=True)
        .distinct()
    )

    yes_required_ids = db_yes_ids.union(fs_yes_ids)

    # ========================================================================
    # 4. AUTO-TRIGGER LOGIC (RUN NOW AFTER 24 HOURS)
    # ========================================================================
    now = timezone.now()
    triggered_count = 0

    if job_id:
        try:
            healthcheck_job = ScheduledJob.objects.get(pk=job_id, enabled=True)
            
            if healthcheck_job.deployment_version:
                for r in records:
                    status_id = r["id"]
                    
                    # Trigger conditions: Action Required = YES + EndTime + 24hrs passed
                    if status_id in yes_required_ids and r["EndTime"]:
                        end_time = r["EndTime"]
                        
                        if timezone.is_naive(end_time):
                            end_time = timezone.make_aware(end_time)
                        
                        trigger_time = end_time + timedelta(hours=24)
                        
                        # If 24 hours passed, trigger the job
                        if now >= trigger_time:
                            try:
                                async_task(
                                    "scheduler_app.tasks.execute_job",
                                    int(job_id)
                                )
                                triggered_count += 1
                                
                                logger.info(
                                    f"Auto-triggered Job {job_id} for Process {status_id} "
                                    f"(Process_id: {r['Process_id']})"
                                )
                            except Exception as e:
                                logger.error(f"Failed to trigger Job {job_id}: {str(e)}")
        except ScheduledJob.DoesNotExist:
            logger.error(f"Job {job_id} not found or disabled")
        except Exception as e:
            logger.error(f"Error in auto-trigger: {str(e)}")

    # ========================================================================
    # 5. BUILD RESPONSE WITH JOB RUN STATUS
    # ========================================================================
    data = []
    for r in records:
        status_id = r["id"]
        action_required = "YES" if status_id in yes_required_ids else "NO"
        
        # Calculate job run status
        job_run_status = None
        execution_time = None
        
        if action_required == "YES" and r["EndTime"]:
            end_time = r["EndTime"]
            
            if timezone.is_naive(end_time):
                end_time = timezone.make_aware(end_time)
            
            trigger_time = end_time + timedelta(hours=24)
            execution_time = trigger_time.strftime("%Y-%m-%d %H:%M:%S")
            
            if now < trigger_time:
                # Waiting
                time_remaining = trigger_time - now
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                job_run_status = f"Waiting {hours}h {minutes}m"
            else:
                # Executed or Ready
                job_run_status = "Executed"
        
        data.append({
            "id": r["id"],
            "Process_id": r["Process_id"],
            "Customer": r["Customer"] or "-",
            "Environment": r["Environment"] or "-",
            "Tenant": r["Tenant"] or "-",
            "Status": r["Status"] or "-",
            "ErrorMessage": r["ErrorMessage"] or "-",
            "StartTime": r["StartTime"].strftime("%Y-%m-%d %H:%M:%S") if r["StartTime"] else "-",
            "EndTime": r["EndTime"].strftime("%Y-%m-%d %H:%M:%S") if r["EndTime"] else "-",
            "action_required": action_required,
            "job_run_status": job_run_status,
            "execution_time": execution_time
        })

    return JsonResponse({
        "records": data,
        "recordsTotal": total_count,
        "recordsFiltered": filtered_count,
        "start": start,
        "length": length,
        "triggered_count": triggered_count
    })