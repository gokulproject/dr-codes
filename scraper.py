{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Audit Log</title>
  <!-- Bootstrap 5 -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
  <!-- Bootstrap Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet"/>

  <style>
    :root {
      --sidebar-w: 260px;
      --brand:     #4f46e5;
      --brand-dk:  #3730a3;
    }

    /* ── Layout ───────────────────────────────── */
    body { background: #f1f5f9; font-size: .92rem; }

    .sidebar {
      width: var(--sidebar-w);
      min-height: 100vh;
      background: #1e1b4b;
      color: #c7d2fe;
      position: fixed;
      top: 0; left: 0;
      display: flex;
      flex-direction: column;
      z-index: 1000;
    }
    .sidebar .brand {
      padding: 1.4rem 1.5rem 1rem;
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
      border-bottom: 1px solid #312e81;
    }
    .sidebar .brand i { color: #818cf8; margin-right: .5rem; }
    .sidebar .nav-section {
      padding: .75rem 1rem .25rem;
      font-size: .7rem;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: #6366f1;
    }
    .sidebar .nav-link {
      padding: .55rem 1.5rem;
      color: #c7d2fe;
      border-radius: 0;
      display: flex;
      align-items: center;
      gap: .6rem;
      transition: background .15s;
    }
    .sidebar .nav-link:hover,
    .sidebar .nav-link.active {
      background: #312e81;
      color: #fff;
    }
    .sidebar .badge-count {
      margin-left: auto;
      background: #4f46e5;
      font-size: .68rem;
    }

    .main-content {
      margin-left: var(--sidebar-w);
      padding: 2rem;
      min-height: 100vh;
    }

    /* ── Topbar ───────────────────────────────── */
    .topbar {
      background: #fff;
      border-radius: .75rem;
      padding: 1rem 1.5rem;
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 1px 4px rgba(0,0,0,.06);
    }
    .topbar h1 { font-size: 1.4rem; font-weight: 700; margin: 0; color: #1e1b4b; }

    /* ── Stat Cards ───────────────────────────── */
    .stat-card {
      border-radius: .75rem;
      padding: 1.2rem 1.5rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .stat-card i { font-size: 2rem; opacity: .8; }
    .stat-card .num  { font-size: 1.8rem; font-weight: 700; line-height: 1; }
    .stat-card .lbl  { font-size: .78rem; opacity: .85; margin-top: .2rem; }
    .bg-crud    { background: linear-gradient(135deg,#6366f1,#4f46e5); }
    .bg-request { background: linear-gradient(135deg,#0ea5e9,#0284c7); }
    .bg-login   { background: linear-gradient(135deg,#10b981,#059669); }

    /* ── Filter Card ──────────────────────────── */
    .filter-card {
      background: #fff;
      border-radius: .75rem;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 4px rgba(0,0,0,.06);
    }
    .filter-card .filter-title {
      font-weight: 600;
      font-size: .85rem;
      color: #4f46e5;
      margin-bottom: .9rem;
      display: flex;
      align-items: center;
      gap: .4rem;
    }

    /* ── Table Card ───────────────────────────── */
    .table-card {
      background: #fff;
      border-radius: .75rem;
      box-shadow: 0 1px 4px rgba(0,0,0,.06);
      overflow: hidden;
    }
    .table-card .card-header-custom {
      background: #fff;
      padding: 1rem 1.5rem;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .table thead th {
      background: #f8fafc;
      font-size: .78rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .05em;
      color: #64748b;
      border-bottom: 2px solid #e2e8f0;
      white-space: nowrap;
    }
    .table tbody tr:hover { background: #f8fafc; }
    .table td { vertical-align: middle; font-size: .85rem; color: #334155; }

    /* ── Badges ───────────────────────────────── */
    .badge-create { background: #d1fae5; color: #065f46; }
    .badge-update { background: #dbeafe; color: #1e40af; }
    .badge-delete { background: #fee2e2; color: #991b1b; }
    .badge-read   { background: #f3f4f6; color: #374151; }
    .badge-login  { background: #d1fae5; color: #065f46; }
    .badge-logout { background: #fef3c7; color: #92400e; }
    .badge-failed { background: #fee2e2; color: #991b1b; }

    /* ── Pagination ───────────────────────────── */
    .pagination .page-link {
      border-radius: .4rem !important;
      margin: 0 2px;
      color: #4f46e5;
      border-color: #e2e8f0;
    }
    .pagination .page-item.active .page-link {
      background: #4f46e5;
      border-color: #4f46e5;
    }

    /* ── Nav tabs override ────────────────────── */
    .nav-tabs .nav-link { color: #64748b; border: none; padding: .6rem 1.2rem; }
    .nav-tabs .nav-link.active {
      color: #4f46e5;
      border-bottom: 2px solid #4f46e5;
      background: transparent;
      font-weight: 600;
    }

    /* ── Responsive ───────────────────────────── */
    @media (max-width: 768px) {
      .sidebar { display: none; }
      .main-content { margin-left: 0; padding: 1rem; }
    }
  </style>
</head>
<body>

<!-- ════════════════════════════════════════════════════════
     SIDEBAR
════════════════════════════════════════════════════════ -->
<div class="sidebar">
  <div class="brand">
    <i class="bi bi-shield-check"></i> AuditTrail
  </div>

  <div class="nav-section">Overview</div>
  <a href="?event_type=crud"
     class="nav-link {% if active_tab == 'crud' %}active{% endif %}">
    <i class="bi bi-database"></i> CRUD Events
    <span class="badge rounded-pill badge-count">{{ total_crud }}</span>
  </a>
  <a href="?event_type=request"
     class="nav-link {% if active_tab == 'request' %}active{% endif %}">
    <i class="bi bi-globe"></i> Request Events
    <span class="badge rounded-pill badge-count">{{ total_request }}</span>
  </a>
  <a href="?event_type=login"
     class="nav-link {% if active_tab == 'login' %}active{% endif %}">
    <i class="bi bi-person-lock"></i> Login Events
    <span class="badge rounded-pill badge-count">{{ total_login }}</span>
  </a>

  <div class="nav-section mt-3">Quick Filters</div>
  <a href="?event_type=crud&crud_action=CREATE" class="nav-link">
    <i class="bi bi-plus-circle text-success"></i> Creates
  </a>
  <a href="?event_type=crud&crud_action=UPDATE" class="nav-link">
    <i class="bi bi-pencil-square text-primary"></i> Updates
  </a>
  <a href="?event_type=crud&crud_action=DELETE" class="nav-link">
    <i class="bi bi-trash text-danger"></i> Deletes
  </a>
  <a href="?event_type=login&login_type=F" class="nav-link">
    <i class="bi bi-exclamation-triangle text-warning"></i> Failed Logins
  </a>

  <div class="mt-auto p-3 border-top" style="border-color:#312e81!important">
    <small class="text-muted d-block">django-easy-audit</small>
    <small style="color:#6366f1">All activity is tracked</small>
  </div>
</div>


<!-- ════════════════════════════════════════════════════════
     MAIN CONTENT
════════════════════════════════════════════════════════ -->
<div class="main-content">

  <!-- Topbar -->
  <div class="topbar">
    <div>
      <h1><i class="bi bi-journal-text me-2" style="color:#4f46e5"></i>Audit Log</h1>
      <small class="text-muted">Full activity trail across your application</small>
    </div>
    <div class="d-flex align-items-center gap-2">
      <span class="badge bg-light text-dark border">
        <i class="bi bi-person-circle me-1"></i>{{ request.user.username }}
      </span>
      <a href="{% url 'admin:index' %}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-grid"></i> Admin
      </a>
    </div>
  </div>

  <!-- Stat Cards -->
  <div class="row g-3 mb-4">
    <div class="col-md-4">
      <div class="stat-card bg-crud">
        <i class="bi bi-database-fill-gear"></i>
        <div>
          <div class="num">{{ total_crud }}</div>
          <div class="lbl">CRUD Events</div>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="stat-card bg-request">
        <i class="bi bi-cloud-arrow-in-fill"></i>
        <div>
          <div class="num">{{ total_request }}</div>
          <div class="lbl">HTTP Requests</div>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="stat-card bg-login">
        <i class="bi bi-person-fill-check"></i>
        <div>
          <div class="num">{{ total_login }}</div>
          <div class="lbl">Login Events</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── FILTER FORM ───────────────────────────────────────────── -->
  <div class="filter-card">
    <div class="filter-title"><i class="bi bi-funnel-fill"></i> Filters</div>

    <form method="get" id="filterForm">
      <!-- Keep active tab when submitting -->
      <input type="hidden" name="event_type" value="{{ event_type }}">

      <div class="row g-3">

        <!-- Search -->
        <div class="col-lg-3 col-md-6">
          <label class="form-label fw-semibold">Search</label>
          <div class="input-group">
            <span class="input-group-text bg-white"><i class="bi bi-search text-muted"></i></span>
            <input type="text" class="form-control" name="search"
                   placeholder="Object, user, URL…"
                   value="{{ filter_search }}">
          </div>
        </div>

        <!-- User -->
        <div class="col-lg-2 col-md-6">
          <label class="form-label fw-semibold">User</label>
          <select class="form-select" name="user_id">
            <option value="">All Users</option>
            {% for u in all_users %}
              <option value="{{ u.pk }}" {% if filter_user_id == u.pk|stringformat:"s" %}selected{% endif %}>
                {{ u.username }}
              </option>
            {% endfor %}
          </select>
        </div>

        <!-- App Label (CRUD only) -->
        {% if active_tab == 'crud' %}
        <div class="col-lg-2 col-md-6">
          <label class="form-label fw-semibold">App</label>
          <select class="form-select" name="app_label" id="appSelect">
            <option value="">All Apps</option>
            {% for a in app_labels %}
              <option value="{{ a }}" {% if filter_app_label == a %}selected{% endif %}>{{ a }}</option>
            {% endfor %}
          </select>
        </div>

        <!-- Model -->
        <div class="col-lg-2 col-md-6">
          <label class="form-label fw-semibold">Model</label>
          <select class="form-select" name="model_name">
            <option value="">All Models</option>
            {% for m in model_names %}
              <option value="{{ m }}" {% if filter_model_name == m %}selected{% endif %}>{{ m }}</option>
            {% endfor %}
          </select>
        </div>

        <!-- CRUD Action -->
        <div class="col-lg-2 col-md-6">
          <label class="form-label fw-semibold">Action</label>
          <select class="form-select" name="crud_action">
            <option value="">All Actions</option>
            <option value="CREATE" {% if filter_crud_action == "CREATE" %}selected{% endif %}>➕ Create</option>
            <option value="READ"   {% if filter_crud_action == "READ"   %}selected{% endif %}>👁 Read</option>
            <option value="UPDATE" {% if filter_crud_action == "UPDATE" %}selected{% endif %}>✏️ Update</option>
            <option value="DELETE" {% if filter_crud_action == "DELETE" %}selected{% endif %}>🗑 Delete</option>
          </select>
        </div>
        {% endif %}

        <!-- Login Type (Login tab only) -->
        {% if active_tab == 'login' %}
        <div class="col-lg-2 col-md-6">
          <label class="form-label fw-semibold">Login Type</label>
          <select class="form-select" name="login_type">
            <option value="">All</option>
            <option value="L"  {% if filter_login_type == "L"  %}selected{% endif %}>✅ Login</option>
            <option value="LO" {% if filter_login_type == "LO" %}selected{% endif %}>🚪 Logout</option>
            <option value="F"  {% if filter_login_type == "F"  %}selected{% endif %}>❌ Failed</option>
          </select>
        </div>
        {% endif %}

        <!-- Date From -->
        <div class="col-lg-2 col-md-6">
          <label class="form-label fw-semibold">Date From</label>
          <input type="date" class="form-control" name="date_from" value="{{ filter_date_from }}">
        </div>

        <!-- Date To -->
        <div class="col-lg-2 col-md-6">
          <label class="form-label fw-semibold">Date To</label>
          <input type="date" class="form-control" name="date_to" value="{{ filter_date_to }}">
        </div>

        <!-- Per Page -->
        <div class="col-lg-1 col-md-4">
          <label class="form-label fw-semibold">Per Page</label>
          <select class="form-select" name="per_page">
            {% for n in "10,25,50,100"|split:"," %}
              <option value="{{ n }}" {% if per_page|stringformat:"s" == n %}selected{% endif %}>{{ n }}</option>
            {% endfor %}
          </select>
        </div>

      </div><!-- /row -->

      <div class="mt-3 d-flex gap-2">
        <button type="submit" class="btn btn-primary btn-sm px-4">
          <i class="bi bi-search me-1"></i> Apply Filters
        </button>
        <a href="?event_type={{ event_type }}" class="btn btn-outline-secondary btn-sm px-4">
          <i class="bi bi-x-circle me-1"></i> Clear
        </a>
      </div>
    </form>
  </div>

  <!-- ── TABLE CARD ────────────────────────────────────────────── -->
  <div class="table-card">
    <!-- Tab Header -->
    <div class="card-header-custom">
      <ul class="nav nav-tabs border-0">
        <li class="nav-item">
          <a class="nav-link {% if active_tab == 'crud' %}active{% endif %}"
             href="?event_type=crud&user_id={{ filter_user_id }}&date_from={{ filter_date_from }}&date_to={{ filter_date_to }}&search={{ filter_search }}">
            <i class="bi bi-database me-1"></i>CRUD
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link {% if active_tab == 'request' %}active{% endif %}"
             href="?event_type=request&user_id={{ filter_user_id }}&date_from={{ filter_date_from }}&date_to={{ filter_date_to }}&search={{ filter_search }}">
            <i class="bi bi-globe me-1"></i>Requests
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link {% if active_tab == 'login' %}active{% endif %}"
             href="?event_type=login&user_id={{ filter_user_id }}&date_from={{ filter_date_from }}&date_to={{ filter_date_to }}&search={{ filter_search }}">
            <i class="bi bi-person-lock me-1"></i>Login
          </a>
        </li>
      </ul>

      <span class="text-muted" style="font-size:.82rem">
        <i class="bi bi-list-ul me-1"></i>
        {{ paginator.count }} record{{ paginator.count|pluralize }}
      </span>
    </div>

    <div class="table-responsive">
      <table class="table table-hover mb-0">

        <!-- ══ CRUD TABLE ══ -->
        {% if active_tab == 'crud' %}
        <thead>
          <tr>
            <th>#</th>
            <th>Date / Time</th>
            <th>Action</th>
            <th>App</th>
            <th>Model</th>
            <th>Object</th>
            <th>User</th>
            <th>Object ID</th>
          </tr>
        </thead>
        <tbody>
          {% for event in page_obj %}
          <tr>
            <td class="text-muted">{{ forloop.counter|add:page_obj.start_index|add:"-1" }}</td>
            <td>
              <span class="d-block">{{ event.datetime|date:"d M Y" }}</span>
              <small class="text-muted">{{ event.datetime|time:"H:i:s" }}</small>
            </td>
            <td>
              {% if event.event_type == CRUD_CREATE %}
                <span class="badge badge-create rounded-pill px-3">CREATE</span>
              {% elif event.event_type == CRUD_UPDATE %}
                <span class="badge badge-update rounded-pill px-3">UPDATE</span>
              {% elif event.event_type == CRUD_DELETE %}
                <span class="badge badge-delete rounded-pill px-3">DELETE</span>
              {% else %}
                <span class="badge badge-read rounded-pill px-3">READ</span>
              {% endif %}
            </td>
            <td><code class="text-indigo">{{ event.content_type.app_label }}</code></td>
            <td>{{ event.content_type.model|title }}</td>
            <td>
              <span title="{{ event.object_repr }}"
                    style="max-width:180px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                {{ event.object_repr }}
              </span>
            </td>
            <td>
              {% if event.user %}
                <i class="bi bi-person-circle me-1 text-muted"></i>{{ event.user.username }}
              {% else %}
                <span class="text-muted">—</span>
              {% endif %}
            </td>
            <td><code>{{ event.object_id }}</code></td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="8" class="text-center text-muted py-5">
              <i class="bi bi-inbox fs-2 d-block mb-2"></i>No CRUD events found
            </td>
          </tr>
          {% endfor %}
        </tbody>

        <!-- ══ REQUEST TABLE ══ -->
        {% elif active_tab == 'request' %}
        <thead>
          <tr>
            <th>#</th>
            <th>Date / Time</th>
            <th>Method</th>
            <th>URL</th>
            <th>User</th>
            <th>IP Address</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {% for event in page_obj %}
          <tr>
            <td class="text-muted">{{ forloop.counter }}</td>
            <td>
              <span class="d-block">{{ event.datetime|date:"d M Y" }}</span>
              <small class="text-muted">{{ event.datetime|time:"H:i:s" }}</small>
            </td>
            <td>
              <span class="badge bg-{% if event.method == 'GET' %}success{% elif event.method == 'POST' %}primary{% elif event.method == 'DELETE' %}danger{% else %}warning{% endif %} rounded-pill">
                {{ event.method }}
              </span>
            </td>
            <td>
              <span title="{{ event.url }}"
                    style="max-width:260px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                {{ event.url }}
              </span>
            </td>
            <td>
              {% if event.user %}
                <i class="bi bi-person-circle me-1 text-muted"></i>{{ event.user.username }}
              {% else %}
                <span class="text-muted fst-italic">Anonymous</span>
              {% endif %}
            </td>
            <td><code>{{ event.remote_ip|default:"—" }}</code></td>
            <td>
              {% if event.response_status_code %}
                <span class="badge {% if event.response_status_code < 300 %}bg-success{% elif event.response_status_code < 400 %}bg-info{% elif event.response_status_code < 500 %}bg-warning text-dark{% else %}bg-danger{% endif %} rounded-pill">
                  {{ event.response_status_code }}
                </span>
              {% else %}
                <span class="text-muted">—</span>
              {% endif %}
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="7" class="text-center text-muted py-5">
              <i class="bi bi-inbox fs-2 d-block mb-2"></i>No request events found
            </td>
          </tr>
          {% endfor %}
        </tbody>

        <!-- ══ LOGI
- ══ LOGIN TABLE ══ -->
        {% elif active_tab == 'login' %}
        <thead>
          <tr>
            <th>#</th>
            <th>Date / Time</th>
            <th>Event</th>
            <th>Username</th>
            <th>User (resolved)</th>
            <th>IP Address</th>
          </tr>
        </thead>
        <tbody>
          {% for event in page_obj %}
          <tr>
            <td class="text-muted">{{ forloop.counter }}</td>
            <td>
              <span class="d-block">{{ event.datetime|date:"d M Y" }}</span>
              <small class="text-muted">{{ event.datetime|time:"H:i:s" }}</small>
            </td>
            <td>
              {% if event.login_type == LOGIN_IN %}
                <span class="badge badge-login rounded-pill px-3"><i class="bi bi-box-arrow-in-right me-1"></i>Login</span>
              {% elif event.login_type == LOGIN_OUT %}
                <span class="badge badge-logout rounded-pill px-3"><i class="bi bi-box-arrow-left me-1"></i>Logout</span>
              {% else %}
                <span class="badge badge-failed rounded-pill px-3"><i class="bi bi-x-circle me-1"></i>Failed</span>
              {% endif %}
            </td>
            <td><strong>{{ event.username|default:"—" }}</strong></td>
            <td>
              {% if event.user %}
                <i class="bi bi-person-circle me-1 text-muted"></i>{{ event.user.username }}
              {% else %}
                <span class="text-muted">—</span>
              {% endif %}
            </td>
            <td><code>{{ event.remote_ip|default:"—" }}</code></td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="6" class="text-center text-muted py-5">
              <i class="bi bi-inbox fs-2 d-block mb-2"></i>No login events found
            </td>
          </tr>
          {% endfor %}
        </tbody>
        {% endif %}

      </table>
    </div>

    <!-- ── Pagination ────────────────────────────────────────── -->
    {% if page_obj.has_other_pages %}
    <div class="d-flex align-items-center justify-content-between px-4 py-3 border-top">
      <small class="text-muted">
        Showing {{ page_obj.start_index }}–{{ page_obj.end_index }} of {{ paginator.count }}
      </small>

      <nav>
        <ul class="pagination pagination-sm mb-0">
          {% if page_obj.has_previous %}
            <li class="page-item">
              <a class="page-link" href="?{% for k,v in request.GET.items %}{% if k != 'page' %}{{ k }}={{ v }}&{% endif %}{% endfor %}page=1">
                <i class="bi bi-chevron-double-left"></i>
              </a>
            </li>
            <li class="page-item">
              <a class="page-link" href="?{% for k,v in request.GET.items %}{% if k != 'page' %}{{ k }}={{ v }}&{% endif %}{% endfor %}page={{ page_obj.previous_page_number }}">
                <i class="bi bi-chevron-left"></i>
              </a>
            </li>
          {% endif %}

          {% for num in paginator.page_range %}
            {% if page_obj.number == num %}
              <li class="page-item active"><span class="page-link">{{ num }}</span></li>
            {% elif num > page_obj.number|add:"-3" and num < page_obj.number|add:"3" %}
              <li class="page-item">
                <a class="page-link" href="?{% for k,v in request.GET.items %}{% if k != 'page' %}{{ k }}={{ v }}&{% endif %}{% endfor %}page={{ num }}">{{ num }}</a>
              </li>
            {% endif %}
          {% endfor %}

          {% if page_obj.has_next %}
            <li class="page-item">
              <a class="page-link" href="?{% for k,v in request.GET.items %}{% if k != 'page' %}{{ k }}={{ v }}&{% endif %}{% endfor %}page={{ page_obj.next_page_number }}">
                <i class="bi bi-chevron-right"></i>
              </a>
            </li>
            <li class="page-item">
              <a class="page-link" href="?{% for k,v in request.GET.items %}{% if k != 'page' %}{{ k }}={{ v }}&{% endif %}{% endfor %}page={{ paginator.num_pages }}">
                <i class="bi bi-chevron-double-right"></i>
              </a>
            </li>
          {% endif %}
        </ul>
      </nav>
    </div>
    {% endif %}

  </div><!-- /table-card -->
</div><!-- /main-content -->

<!-- Auto-reload app → model dropdown when app changes -->
<script>
  document.getElementById('appSelect')?.addEventListener('change', function () {
    const form = document.getElementById('filterForm');
    // clear model so it refreshes server-side
    const modelSel = form.querySelector('[name="model_name"]');
    if (modelSel) modelSel.value = '';
    form.submit();
  });
</script>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>