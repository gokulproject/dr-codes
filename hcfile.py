{% load static %} {% load django_bootstrap5 %} 
<!DOCTYPE html> 
<html lang="en"> 
<head> 
<meta charset="UTF-8"> 
<meta name="viewport" content="width=device-width, initial-scale=1.0"> 
<title>Healthcheck Dashboard - {{ job.name }}</title> 
{% bootstrap_css %} 
<style> 
body { background: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding-top: 120px; } 
.card { border: none; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } 
.table th { background: #e9ecef; font-weight: 600; position: sticky; top: 0; z-index: 10; } 
.table td, .table th { vertical-align: middle; padding: 0.6rem 0.5rem; } 
.table-container { max-height: 500px; overflow: auto; } 
.status-success { background-color: #d4edda !important; } 
.status-failed { background-color: #f8d7da !important; } 
.status-running { background-color: #fff3cd !important; } 
.badge.fs-6 { font-size: 1rem !important; } 
.job-updating { opacity: 0.7; } 
.search-pill { border-radius: 999px; } 
.page-link { cursor: pointer; } 
.spinner-overlay { position: absolute; inset: 0; background: rgba(255,255,255,0.8); display: flex; justify-content: center; align-items: center; z-index: 50; }
/* NEW STYLES FOR ACTION REQUIRED */
.action-check { transition: all 0.2s; font-size: 0.8rem; }
.action-yes { background: #f8d7da !important; color: #721c24; border-color: #f5c6cb; }
.action-no { background: #d4edda !important; color: #155724; border-color: #c3e6cb; }
.action-loading { opacity: 0.6; }
</style> 
</head> 
<body> 
<header>{% include "healthcheckapp/hc_navbar.html" %}</header> 
<div class="container-fluid py-4"> 
<h5 class="mb-1">{{ job.name }}</h5> 

<!-- Job Status (UNCHANGED) --> 
<div class="card mb-4"> 
<div class="card-header d-flex justify-content-between align-items-center"> 
<small class="text-muted" id="job-updated">Job status</small> 
</div> 
<div class="card-body p-0 job-updating" id="jobStatusCard"> 
<div class="table-responsive"> 
<table class="table table-striped table-hover mb-0" id="jobStatusTable"> 
<thead class="table-light"><tr><th>Status</th><th>Last Run</th><th>Next Run</th></tr></thead> 
<tbody><tr class="text-center text-muted"><td colspan="3" class="py-4"><small>Loading...</small></td></tr></tbody> 
</table> 
</div> 
</div> 
</div> 

<!-- Process Table (UPDATED: Added Action Required column + click handlers) --> 
<div class="card position-relative" id="processCard"> 
<div class="spinner-overlay d-none" id="processSpinner"> 
<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div> 
</div> 
<div class="card-header"> 
<div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2"> 
<h6 class="mb-0">Process Status</h6> 
<div class="input-group input-group-sm" style="max-width: 320px;"> 
<span class="input-group-text bg-white border-end-0"><i class="bi bi-search"></i></span> 
<input type="text" id="globalSearch" class="form-control border-start-0 search-pill" placeholder="Search customer, env, tenant, status..."> 
<button class="btn btn-outline-secondary" type="button" id="btnClearSearch">×</button> 
</div> 
</div> 
<!-- Advanced Filters (UNCHANGED) --> 
<div class="mt-2"> 
<button class="btn btn-link btn-sm p-0" type="button" data-bs-toggle="collapse" data-bs-target="#advancedFilters"> Advanced filters </button> 
<div class="collapse mt-2" id="advancedFilters"> 
<div class="row g-2"> 
<div class="col-md-3"><input type="text" id="filterCustomer" class="form-control form-control-sm" placeholder="Customer"></div> 
<div class="col-md-3"><input type="text" id="filterEnv" class="form-control form-control-sm" placeholder="Environment"></div> 
<div class="col-md-2"><input type="date" id="filterStartDate" class="form-control form-control-sm"></div> 
<div class="col-md-2"><input type="date" id="filterEndDate" class="form-control form-control-sm"></div> 
<div class="col-md-2 d-flex"> 
<button id="btnApplyFilter" class="btn btn-sm btn-primary me-2 flex-fill">Apply</button> 
<button id="btnClearFilter" class="btn btn-sm btn-outline-secondary flex-fill">Reset</button> 
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
<th style="width: 120px;">Action Required</th>  <!-- UPDATED: Wider for badge -->
</tr> 
</thead> 
<tbody></tbody> 
</table> 
<!-- Numbered Pagination (UNCHANGED) --> 
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
const DB_REPORT_API = "{% url 'healthcheckapp:hc_database_report_api' 0 %}".replace(/0\/$/, '/');  // NEW
const FS_REPORT_API = "{% url 'healthcheckapp:hc_filesystem_report_api' 0 %}".replace(/0\/$/, '/');  // NEW
const RECORDS_BASE_URL = "{% url 'healthcheckapp:records' 0 %}".replace(/0\/$/, ''); 
let start = 0, length = 10, total = 0, firstLoadDone = false; 
let filterCustomer = '', filterEnv = '', filterStartDate = '', filterEndDate = '', globalSearch = ''; 

function setSpinner(visible) { 
document.getElementById('processSpinner').classList.toggle('d-none', !visible); 
} 

function updatePagination() { 
// UNCHANGED - same as original
const bar = document.getElementById('paginationBar'), info = document.getElementById('pageInfo'); 
bar.innerHTML = ''; 
const currentPage = Math.floor(start / length) + 1, totalPages = Math.ceil(total / length) || 1; 
info.textContent = `Page ${currentPage} of ${totalPages} • ${total.toLocaleString()} total`; 
function addPage(label, page, disabled = false, active = false) { 
const li = document.createElement('li'); 
li.className = `page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}`; 
const a = document.createElement('a'); 
a.className = 'page-link', a.textContent = label; 
if (!disabled && !active) { 
a.addEventListener('click', () => { start = (page - 1) * length; fetchProcessPage(); }); 
} 
li.appendChild(a); bar.appendChild(li); 
} 
addPage('« Prev', currentPage - 1, currentPage === 1); 
const windowSize = 5, startPage = Math.max(1, currentPage - 2), endPage = Math.min(totalPages, startPage + windowSize - 1); 
if (startPage > 1) { addPage('1', 1, false, currentPage === 1); if (startPage > 2) addPage('...', 1, true); } 
for (let p = startPage; p <= endPage; p++) addPage(p.toString(), p, false, p === currentPage); 
if (endPage < totalPages) { if (endPage < totalPages - 1) addPage('...', totalPages, true); addPage(totalPages.toString(), totalPages, false, currentPage === totalPages); } 
addPage('Next »', currentPage + 1, currentPage === totalPages); 
} 

// NEW: Check Action Required for a status_id
function checkActionRequired(statusId, cell) {
    cell.innerHTML = '<span class="spinner-border spinner-border-sm action-loading" style="width:1rem;height:1rem;"></span>';
    
    // Parallel API calls
    Promise.all([
        fetch(`${DB_REPORT_API}${statusId}/`),
        fetch(`${FS_REPORT_API}${statusId}/`)
    ]).then(([dbRes, fsRes]) => Promise.all([dbRes.json(), fsRes.json()]))
    .then(([dbData, fsData]) => {
        const dbYes = dbData.records[0]?.yes_count || 0;
        const fsYes = fsData.records[0]?.yes_count || 0;
        const totalYes = dbYes + fsYes;
        const isRequired = totalYes >= 1;
        
        cell.innerHTML = `<span class="badge fs-6 ${isRequired ? 'bg-danger action-yes' : 'bg-success action-no'}">
            ${isRequired ? 'YES' : 'NO'} (${totalYes})
        </span>`;
        cell.title = `DB: ${dbYes}, FS: ${fsYes} actions needed`;
    }).catch(() => {
        cell.innerHTML = '<span class="badge bg-secondary">Error</span>';
    });
}

function updateProcessTable(data) { 
const tbody = document.querySelector('#processTable tbody'); 
tbody.innerHTML = ''; 
total = data.recordsFiltered || data.recordsTotal || 0; 
if (!data.records?.length) { 
tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4 text-muted">No data found</td></tr>';  // UPDATED: colspan=10
} else { 
data.records.forEach((r, i) => { 
const row = document.createElement('tr'); 
row.className = r.Status === 'Success' ? 'status-success' : r.Status === 'Failed' ? 'status-failed' : r.Status === 'Running' ? 'status-running' : ''; 
row.innerHTML = ` 
<td>${start + i + 1}</td> 
<td>${r.Customer || '-'}</td> 
<td><span class="badge bg-info">${r.Environment || '-'}</span></td> 
<td>${r.Tenant || '-'}</td> 
<td><span class="badge ${r.Status === 'Success' ? 'bg-success' : r.Status === 'Failed' ? 'bg-danger' : r.Status === 'Running' ? 'bg-warning' : 'bg-success'}">${r.Status || '-'}</span></td> 
<td>${r.ErrorMessage || '-'}</td> 
<td>${r.StartTime || '-'}</td> 
<td>${r.EndTime || '-'}</td> 
<td><a href="${RECORDS_BASE_URL}${r.id}/?job_id={{ job.id }}" class="btn btn-sm btn-outline-info">View</a></td> 
<td class="action-cell text-center" data-status-id="${r.id}">  <!-- NEW: Action cell -->
    <button class="btn btn-sm btn-outline-secondary action-check" data-id="${r.id}">Check</button>
</td> 
`; 
tbody.appendChild(row); 
}); 
} 
updatePagination(); 

// NEW: Bind click handlers AFTER table update
document.querySelectorAll('.action-check').forEach(btn => {
    btn.addEventListener('click', function() {
        const statusId = this.dataset.id;
        const cell = this.closest('td');
        checkActionRequired(statusId, cell);
        this.remove();  // Remove button after click
    });
});
} 

function fetchProcessPage() { 
setSpinner(!firstLoadDone); 
const params = new URLSearchParams({ start: start, length: length }); 
if (filterCustomer) params.append('customer', filterCustomer); 
if (filterEnv) params.append('env', filterEnv); 
if (filterStartDate) params.append('start_date', filterStartDate); 
if (filterEndDate) params.append('end_date', filterEndDate); 
if (globalSearch) params.append('search', globalSearch); 
fetch(`${PROCESS_API}?${params}`).then(r => r.json()).then(data => { 
updateProcessTable(data); 
firstLoadDone = true; 
setSpinner(false); 
}).catch(err => { 
console.error(err); 
setSpinner(false); 
}); 
} 

// Event handlers (UNCHANGED) 
document.getElementById('globalSearch').addEventListener('input', function() { 
globalSearch = this.value.trim(); start = 0; fetchProcessPage(); 
}); 
document.getElementById('btnClearSearch').addEventListener('click', () => { 
document.getElementById('globalSearch').value = ''; globalSearch = ''; start = 0; fetchProcessPage(); 
}); 
document.getElementById('btnApplyFilter').addEventListener('click', () => { 
filterCustomer = document.getElementById('filterCustomer').value.trim(); 
filterEnv = document.getElementById('filterEnv').value.trim(); 
filterStartDate = document.getElementById('filterStartDate').value; 
filterEndDate = document.getElementById('filterEndDate').value; 
start = 0; fetchProcessPage(); 
}); 
document.getElementById('btnClearFilter').addEventListener('click', () => { 
document.getElementById('filterCustomer').value = document.getElementById('filterEnv').value = ''; 
document.getElementById('filterStartDate').value = document.getElementById('filterEndDate').value = ''; 
filterCustomer = filterEnv = filterStartDate = filterEndDate = ''; 
start = 0; fetchProcessPage(); 
}); 

// Job status refresh (UNCHANGED) 
function refreshJobStatus() { 
fetch("{% url 'healthcheckapp:job_status_api' job.id %}").then(r => r.json()).then(data => { 
const tbody = document.querySelector('#jobStatusTable tbody'); 
const card = document.getElementById('jobStatusCard'); 
card.classList.remove('job-updating'); 
const badgeClass = data.status === 'Running' ? 'bg-danger' : 'bg-success'; 
tbody.innerHTML = `<tr><td><span class="badge fs-6 ${badgeClass}">${data.status}</span></td><td>${data.last_run}</td><td>${data.next_run}</td></tr>`; 
}).catch(console.error); 
} 
fetchProcessPage(); 
refreshJobStatus(); 
setInterval(refreshJobStatus, 5000); 
}); 
</script> 
</body> 
</html>
