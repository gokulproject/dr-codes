document.addEventListener('DOMContentLoaded', function () {

  // ── Inject Bootstrap Modal HTML ─────────────────────────────────────────
  const modalHtml = `
  <div class="modal fade" id="auditDetailModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-xl modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header bg-dark text-white">
          <h5 class="modal-title">
            <i class="bi bi-journal-text me-2"></i> Activity Log Details
          </h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body p-0" id="auditModalBody">
          <div class="text-center p-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted">Loading details...</p>
          </div>
        </div>
        <div class="modal-footer bg-light">
          <small class="text-muted me-auto">
            <i class="bi bi-info-circle me-1"></i>
            This log is read-only. Contact your administrator if you have questions.
          </small>
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>`;
  document.body.insertAdjacentHTML('beforeend', modalHtml);

  const modalEl   = document.getElementById('auditDetailModal');
  const modalBody = document.getElementById('auditModalBody');
  const bsModal   = new bootstrap.Modal(modalEl);

  // ── Helpers ─────────────────────────────────────────────────────────────

  function prettifyKey(key) {
    return key
      .replace(/_id$/, '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  }

  function actionBadge(action) {
    const map = {
      'Create' : ['bg-success', 'bi-plus-circle-fill',  'Created'],
      'Update' : ['bg-warning text-dark', 'bi-pencil-fill', 'Updated'],
      'Delete' : ['bg-danger',  'bi-trash-fill',        'Deleted'],
      'Access' : ['bg-info',    'bi-eye-fill',          'Viewed'],
    };
    for (const [key, [cls, icon, label]] of Object.entries(map)) {
      if (action.toLowerCase().includes(key.toLowerCase())) {
        return `<span class="badge ${cls} fs-6 px-3 py-2">
                  <i class="bi ${icon} me-1"></i>${label}
                </span>`;
      }
    }
    return `<span class="badge bg-secondary fs-6 px-3 py-2">${action}</span>`;
  }

  function formatValue(value) {
    if (value === null || value === undefined || value === '')
      return `<span class="text-muted fst-italic">Not set</span>`;
    if (typeof value === 'boolean')
      return value
        ? `<span class="badge bg-success">Yes</span>`
        : `<span class="badge bg-secondary">No</span>`;
    if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/))
      return `<i class="bi bi-calendar2 me-1 text-muted"></i>${value}`;
    return `<span>${value}</span>`;
  }

  // Resolve FK id → human name via Django admin
  async function resolveId(app, model, id) {
    try {
      const res = await fetch(`/admin/${app}/${model}/${id}/change/`, {
        credentials: 'same-origin'
      });
      if (!res.ok) return null;
      const html = await res.text();
      const doc  = new DOMParser().parseFromString(html, 'text/html');
      const h1   = doc.querySelector('#content h1');
      if (h1) return h1.textContent.replace(/^Change\s+/i, '').trim();
    } catch (_) {}
    return null;
  }

  // Resolve an entire snapshot fields object — returns { key: displayValue }
  async function resolveSnapshotFields(app, fields) {
    const entries = await Promise.all(
      Object.entries(fields).map(async ([key, value]) => {
        if (key.endsWith('_id') && value !== null && value !== '') {
          const modelName = key.replace(/_id$/, '');
          const name = await resolveId(app, modelName, value);
          return [key, name ?? value, true];   // [key, resolvedDisplay, isFk]
        }
        return [key, value, false];
      })
    );
    return entries;
  }

  // Build snapshot table rows (awaited)
  async function buildSnapshotRows(app, snapshotJson) {
    let data;
    try { data = JSON.parse(snapshotJson); } catch { return null; }
    const fields = Array.isArray(data) ? (data[0]?.fields ?? {}) : data;
    const entries = await resolveSnapshotFields(app, fields);

    return entries.map(([key, value, isFk]) => {
      const label   = prettifyKey(key);
      const display = isFk
        ? (value
            ? `<span class="text-success fw-semibold">${value}</span>`
            : `<span class="text-muted fst-italic">Not set</span>`)
        : formatValue(value);

      return `
        <tr>
          <td class="fw-semibold text-secondary ps-3" style="width:35%;">
            <i class="bi bi-dot me-1"></i>${label}
          </td>
          <td class="pe-3">${display}</td>
        </tr>`;
    }).join('');
  }

  // Build changed-fields rows
  async function buildChangedRows(app, changesJson) {
    let ch;
    try { ch = JSON.parse(changesJson); } catch { return ''; }
    if (!ch || !Object.keys(ch).length) return '';

    const rows = await Promise.all(
      Object.entries(ch).map(async ([key, value]) => {
        const label = prettifyKey(key);
        let before  = Array.isArray(value) ? value[0] : '—';
        let after   = Array.isArray(value) ? value[1] : value;

        // Resolve FK values
        if (key.endsWith('_id')) {
          const model = key.replace(/_id$/, '');
          if (before && before !== '—') {
            const n = await resolveId(app, model, before);
            if (n) before = n;
          }
          if (after && after !== '—') {
            const n = await resolveId(app, model, after);
            if (n) after = n;
          }
        }

        const beforeHtml = (before === null || before === '' || before === '—')
          ? `<span class="text-muted fst-italic">Not set</span>`
          : `<span class="text-danger">${before}</span>`;

        const afterHtml = (after === null || after === '' || after === '—')
          ? `<span class="text-muted fst-italic">Not set</span>`
          : `<span class="text-success fw-semibold">${after}</span>`;

        return `
          <tr>
            <td class="fw-semibold ps-3" style="width:30%;">
              <i class="bi bi-arrow-right-circle me-1 text-primary"></i>${label}
            </td>
            <td class="text-center">${beforeHtml}</td>
            <td class="text-center">${afterHtml}</td>
          </tr>`;
      })
    );
    return rows.join('');
  }

  // ── Button click ─────────────────────────────────────────────────────────
  document.querySelectorAll('.view-audit-btn').forEach(btn => {
    btn.addEventListener('click', async function () {
      const datetime = this.dataset.datetime || '—';
      const action   = this.dataset.action   || '—';
      const app      = this.dataset.app      || '';
      const model    = this.dataset.model    || '—';
      const object   = this.dataset.object   || '—';
      const user     = this.dataset.user     || 'System';
      const changes  = this.dataset.changes  || '{}';
      const snapshot = this.dataset.snapshot || '{}';

      const modelLabel = model.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

      // Show modal with spinner
      modalBody.innerHTML = `
        <div class="text-center p-5">
          <div class="spinner-border text-primary" role="status"></div>
          <p class="mt-3 text-muted">Resolving record names, please wait…</p>
        </div>`;
      bsModal.show();

      // Fetch all resolved data in parallel
      const [changedRows, snapshotRows] = await Promise.all([
        buildChangedRows(app, changes),
        buildSnapshotRows(app, snapshot),
      ]);

      // ── Compose full modal body ───────────────────────────────────────
      modalBody.innerHTML = `

        <!-- ① WHAT HAPPENED banner -->
        <div class="p-4 border-bottom bg-light d-flex flex-wrap align-items-center gap-3">
          <div>${actionBadge(action)}</div>
          <div>
            <div class="fw-bold fs-5">${object}</div>
            <div class="text-muted small">
              <i class="bi bi-table me-1"></i>${modelLabel} &nbsp;|&nbsp;
              <i class="bi bi-person me-1"></i>${user} &nbsp;|&nbsp;
              <i class="bi bi-clock me-1"></i>${datetime}
            </div>
          </div>
        </div>

        <div class="p-4">

          <!-- ② SUMMARY CARDS -->
          <div class="row g-3 mb-4">
            <div class="col-sm-6 col-md-3">
              <div class="card border-0 bg-primary bg-opacity-10 h-100">
                <div class="card-body py-3">
                  <div class="text-primary small fw-semibold text-uppercase">Action</div>
                  <div class="fw-bold">${action}</div>
                </div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="card border-0 bg-success bg-opacity-10 h-100">
                <div class="card-body py-3">
                  <div class="text-success small fw-semibold text-uppercase">Record</div>
                  <div class="fw-bold">${object}</div>
                </div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="card border-0 bg-warning bg-opacity-10 h-100">
                <div class="card-body py-3">
                  <div class="text-warning small fw-semibold text-uppercase">Done By</div>
                  <div class="fw-bold">${user}</div>
                </div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="card border-0 bg-info bg-opacity-10 h-100">
                <div class="card-body py-3">
                  <div class="text-info small fw-semibold text-uppercase">Module</div>
                  <div class="fw-bold">${modelLabel}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- ③ WHAT CHANGED (only on Update) -->
          ${changedRows ? `
          <div class="card mb-4 border-warning">
            <div class="card-header bg-warning bg-opacity-10 fw-bold text-warning-emphasis">
              <i class="bi bi-pencil-square me-2"></i>What Was Changed
            </div>
            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-sm table-hover align-middle mb-0">
                  <thead class="table-light">
                    <tr>
                      <th class="ps-3">Field</th>
                      <th class="text-center">Previous Value</th>
                      <th class="text-center">New Value</th>
                    </tr>
                  </thead>
                  <tbody>${changedRows}</tbody>
                </table>
              </div>
            </div>
          </div>` : `
          <div class="alert alert-light border mb-4">
            <i class="bi bi-info-circle me-2 text-muted"></i>
            <span class="text-muted">No individual field changes recorded for this action.</span>
          </div>`}

          <!-- ④ FULL RECORD SNAPSHOT -->
          ${snapshotRows ? `
          <div class="card border-secondary border-opacity-25">
            <div class="card-header bg-secondary bg-opacity-10 fw-bold text-secondary">
              <i class="bi bi-card-list me-2"></i>Full Record Details
              <small class="fw-normal ms-2 text-muted">— All field values at the time of this action</small>
            </div>
            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-sm table-striped table-hover align-middle mb-0">
                  <thead class="table-dark">
                    <tr>
                      <th class="ps-3">Field Name</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>${snapshotRows}</tbody>
                </table>
              </div>
            </div>
          </div>` : ''}

        </div><!-- /p-4 -->
      `;
    });
  });

});