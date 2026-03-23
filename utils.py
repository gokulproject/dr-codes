. navitas/registry.py
# navitas/registry.py

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
    'users': {
        'name': 'User Management',
        'description': 'Manage users, roles and permissions',
        'icon': 'bi-people',
        'icon_color': '#6f42c1',
        'url_name': 'users:dashboard',
        'url_prefix': '/users/',
        'color': 'purple',
        'version': '1.0',
    },
    # Add more apps here...
}



_________

# navitas/models.py

from django.db import models


class RegisteredApp(models.Model):
    """
    Database-backed app registry.
    Replaces the static NAVITAS_APPS dict so everything is UI-managed.
    Auto-populated from navitas.registry on first run.
    """
    slug         = models.SlugField(max_length=50, unique=True, help_text='Unique app identifier (e.g. ectd)')
    name         = models.CharField(max_length=100)
    description  = models.TextField(blank=True)
    icon         = models.CharField(max_length=80, default='bi-app', help_text='Bootstrap icon class')
    icon_color   = models.CharField(max_length=20, default='#0d6efd')
    url_name     = models.CharField(max_length=100, help_text='Django URL name for the app dashboard')
    url_prefix   = models.CharField(max_length=100, help_text='URL prefix like /ectd/')
    color        = models.CharField(max_length=20, default='primary')
    version      = models.CharField(max_length=20, blank=True, default='1.0')
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Registered Application'

    def __str__(self):
        return f'{self.name} ({self.slug})'

    @classmethod
    def sync_from_registry(cls):
        """Sync apps from navitas.registry NAVITAS_APPS dict into DB."""
        from navitas.registry import NAVITAS_APPS
        for slug, cfg in NAVITAS_APPS.items():
            cls.objects.update_or_create(
                slug=slug,
                defaults={
                    'name':        cfg.get('name', slug),
                    'description': cfg.get('description', ''),
                    'icon':        cfg.get('icon', 'bi-app'),
                    'icon_color':  cfg.get('icon_color', '#0d6efd'),
                    'url_name':    cfg.get('url_name', ''),
                    'url_prefix':  cfg.get('url_prefix', f'/{slug}/'),
                    'color':       cfg.get('color', 'primary'),
                    'version':     cfg.get('version', '1.0'),
                }
            )




_________


# navitas/admin.py

import json
from django import forms
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from .models import RegisteredApp
from navitas.registry import NAVITAS_APPS


# ─── Custom Form with Slug Dropdown ───────────────────────────────────────────

class RegisteredAppAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Build choices from NAVITAS_APPS
        app_choices = [('', '---------')] + [
            (slug, f"{cfg.get('name', slug)}  [{slug}]")
            for slug, cfg in NAVITAS_APPS.items()
        ]
        self.fields['slug'].widget = forms.Select(choices=app_choices)
        self.fields['slug'].widget.attrs.update({
            'id': 'id_slug',
            'style': 'min-width: 250px;',
        })

    class Meta:
        model = RegisteredApp
        fields = '__all__'

    class Media:
        js = ('admin/js/registered_app_autofill.js',)


# ─── UserGroupMembership Inline (keep your existing one) ─────────────────────

# If you have UserGroupMembership model:
# class UserGroupMembershipInline(admin.TabularInline):
#     model = UserGroupMembership
#     extra = 1
#     raw_id_fields = ('user', 'added_by')


# ─── RegisteredApp Admin ──────────────────────────────────────────────────────

@admin.register(RegisteredApp)
class RegisteredAppAdmin(admin.ModelAdmin):
    form          = RegisteredAppAdminForm
    list_display  = ('name', 'slug', 'url_prefix', 'version', 'is_active', 'display_order')
    list_filter   = ('is_active',)
    search_fields = ('name', 'slug')
    list_editable = ('is_active', 'display_order')
    actions       = ['sync_from_registry']

    # Group fields nicely in the form
    fieldsets = (
        ('App Identity', {
            'fields': ('slug', 'name', 'description', 'version', 'is_active', 'display_order')
        }),
        ('Appearance', {
            'fields': ('icon', 'icon_color', 'color')
        }),
        ('Routing', {
            'fields': ('url_name', 'url_prefix')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'app-registry-data/',
                self.admin_site.admin_view(self.app_registry_data),
                name='registeredapp_registry_data'
            ),
        ]
        return custom_urls + urls

    def app_registry_data(self, request):
        """Return NAVITAS_APPS as JSON — used by autofill JS."""
        return JsonResponse(NAVITAS_APPS)

    def sync_from_registry(self, request, queryset):
        RegisteredApp.sync_from_registry()
        self.message_user(request, 'Apps synced from navitas/registry.py ✓')
    sync_from_registry.short_description = 'Sync apps from code registry'



_________



// your_app/static/admin/js/registered_app_autofill.js

(function () {
  'use strict';

  // Django form field ID  →  key inside NAVITAS_APPS config
  const FIELD_MAP = {
    'name':         'name',
    'description':  'description',
    'icon':         'icon',
    'icon_color':   'icon_color',
    'url_name':     'url_name',
    'url_prefix':   'url_prefix',
    'color':        'color',
    'version':      'version',
  };

  // Fallback values if key is missing for that app
  const DEFAULTS = {
    'icon':        'bi-app',
    'icon_color':  '#0d6efd',
    'color':       'primary',
    'version':     '1.0',
    'description': '',
    'url_name':    '',
    'url_prefix':  '',
    'name':        '',
  };

  let appsData = {};

  // ── Fill all fields based on selected slug ──────────────────────────────────
  function fillFields(slug) {
    if (!slug) {
      clearFields();
      return;
    }

    const cfg = appsData[slug] || {};

    for (const [fieldName, cfgKey] of Object.entries(FIELD_MAP)) {
      const el = document.getElementById('id_' + fieldName);
      if (!el) continue;

      const value = cfg[cfgKey] !== undefined
        ? cfg[cfgKey]
        : (DEFAULTS[cfgKey] !== undefined ? DEFAULTS[cfgKey] : '');

      el.value = value;

      // Notify Django admin widgets of the change
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input',  { bubbles: true }));
    }

    // Auto-generate url_prefix from slug if not defined
    const urlPrefixEl = document.getElementById('id_url_prefix');
    if (urlPrefixEl && !cfg['url_prefix']) {
      urlPrefixEl.value = `/${slug}/`;
    }
  }

  // ── Clear all fields when blank option is selected ──────────────────────────
  function clearFields() {
    for (const fieldName of Object.keys(FIELD_MAP)) {
      const el = document.getElementById('id_' + fieldName);
      if (el) {
        el.value = '';
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
  }

  // ── Build the registry data URL dynamically ─────────────────────────────────
  function getRegistryUrl() {
    const pathname = window.location.pathname;
    const base = pathname.split('/registeredapp/')[0];
    return base + '/registeredapp/app-registry-data/';
  }

  // ── Main init ───────────────────────────────────────────────────────────────
  function init() {
    const slugSelect = document.getElementById('id_slug');
    if (!slugSelect) return;

    // Load all app data from Django admin endpoint
    fetch(getRegistryUrl())
      .then(response => {
        if (!response.ok) throw new Error('Registry fetch failed');
        return response.json();
      })
      .then(data => {
        appsData = data;
        console.log('[Navitas] App registry loaded:', Object.keys(appsData));
      })
      .catch(err => {
        console.warn('[Navitas] Could not load app registry data:', err);
      });

    // Auto-fill on selection change
    slugSelect.addEventListener('change', function () {
      fillFields(this.value);
    });
  }

  // ── Boot ────────────────────────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();





navitas/
├── __init__.py
├── registry.py                          ← all your app configs
├── models.py                            ← RegisteredApp model
├── admin.py                             ← admin + autofill form
└── static/
    └── admin/
        └── js/
            └── registered_app_autofill.js   ← autofill JS
6. Final Steps
# 1. Run migrations
python manage.py makemigrations
python manage.py migrate

# 2. Collect static files
python manage.py collectstatic

# 3. Sync apps from registry into DB (first time)
python manage.py shell
>>> from navitas.models import RegisteredApp
>>> RegisteredApp.sync_from_registry()