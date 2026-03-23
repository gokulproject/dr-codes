# admin.py
import json
from django import forms
from django.http import JsonResponse
from django.urls import path
from navitas.registry import NAVITAS_APPS

class RegisteredAppAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app_choices = [('', '---------')] + [
            (slug, f"{cfg.get('name', slug)} ({slug})")
            for slug, cfg in NAVITAS_APPS.items()
        ]
        self.fields['slug'].widget = forms.Select(choices=app_choices)
        self.fields['slug'].widget.attrs['id'] = 'id_slug'

    class Meta:
        model = RegisteredApp
        fields = '__all__'

    class Media:
        js = ('admin/js/registered_app_autofill.js',)


@admin.register(RegisteredApp)
class RegisteredAppAdmin(admin.ModelAdmin):
    form = RegisteredAppAdminForm
    list_display = ('name', 'slug', 'url_prefix', 'version', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    list_editable = ('is_active', 'display_order')
    prepopulated_fields = {}          # remove this since slug is now a select
    actions = ['sync_from_registry']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('app-registry-data/', self.admin_site.admin_view(self.app_registry_data), name='app_registry_data'),
        ]
        return custom + urls

    def app_registry_data(self, request):
        """Return NAVITAS_APPS as JSON for the autofill JS."""
        return JsonResponse(NAVITAS_APPS)

    def sync_from_registry(self, request, queryset):
        RegisteredApp.sync_from_registry()
        self.message_user(request, 'Apps synced from navitas/registry.py ✓')
    sync_from_registry.short_description = 'Sync apps from code registry'





----****------

// static/admin/js/registered_app_autofill.js
(function () {
  'use strict';

  // Map: Django model field name → key in your NAVITAS_APPS config dict
  const FIELD_MAP = {
    'name':        'name',
    'description': 'description',
    'icon':        'icon',
    'icon_color':  'icon_color',
    'url_name':    'url_name',
    'url_prefix':  'url_prefix',
    'color':       'color',
    'version':     'version',
  };

  // Default fallbacks if a key is missing for that app
  const DEFAULTS = {
    'icon':       'bi-app',
    'icon_color': '#0d6efd',
    'color':      'primary',
    'version':    '1.0',
    'description': '',
    'url_name':   '',
    'url_prefix': '',
  };

  let appsData = {};

  function fillFields(slug) {
    if (!slug) return;

    const cfg = appsData[slug] || {};

    for (const [fieldName, cfgKey] of Object.entries(FIELD_MAP)) {
      const el = document.getElementById('id_' + fieldName);
      if (!el) continue;

      // Use app value → fallback to default → fallback to empty
      const value = cfg[cfgKey] !== undefined
        ? cfg[cfgKey]
        : (DEFAULTS[cfgKey] !== undefined ? DEFAULTS[cfgKey] : '');

      el.value = value;

      // Trigger change event so Django admin widgets react (e.g. prepopulated)
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input',  { bubbles: true }));
    }

    // Auto-fill url_prefix from slug if not in config
    const urlPrefixEl = document.getElementById('id_url_prefix');
    if (urlPrefixEl && !cfg['url_prefix']) {
      urlPrefixEl.value = `/${slug}/`;
    }
  }

  function clearFields() {
    for (const fieldName of Object.keys(FIELD_MAP)) {
      const el = document.getElementById('id_' + fieldName);
      if (el) el.value = '';
    }
  }

  function getRegistryUrl() {
    // Works for both /add/ and /change/<id>/ pages
    const base = window.location.pathname
      .split('/registeredapp/')[0];
    return base + '/registeredapp/app-registry-data/';
  }

  function init() {
    const slugSelect = document.getElementById('id_slug');
    if (!slugSelect) return;

    fetch(getRegistryUrl())
      .then(r => r.json())
      .then(data => {
        appsData = data;
        console.log('Loaded app registry:', Object.keys(appsData));
      })
      .catch(err => console.warn('Could not load app registry data:', err));

    slugSelect.addEventListener('change', function () {
      if (this.value) {
        fillFields(this.value);
      } else {
        clearFields();
      }
    });
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init();
})();

_________

navitas/registry.py

NAVITAS_APPS = {
    'ectd': {
        'name': 'eCTD Manager',
        'description': 'Manage electronic Common Technical Documents',
        'icon': 'bi-file-earmark-text',
        'icon_color': '#0d6efd',
        'url_name': 'ectd:dashboard',
        'url_prefix': '/ectd/',
        'color': 'primary',
        'version': '2.1',
    },
    'safety': {
        'name': 'Safety Reports',
        'description': 'Pharmacovigilance and adverse event tracking',
        'icon': 'bi-shield-check',
        'icon_color': '#dc3545',
        'url_name': 'safety:dashboard',
        'url_prefix': '/safety/',
        'color': 'danger',
        'version': '1.3',
    },
    'analytics': {
        'name': 'Analytics',
        'description': 'Data insights and reporting dashboard',
        'icon': 'bi-bar-chart-line',
        'icon_color': '#198754',
        'url_name': 'analytics:dashboard',
        'url_prefix': '/analytics/',
        'color': 'success',
        'version': '1.0',
    },
    # ... add all your apps
}


from navitas.registry import NAVITAS_APPS