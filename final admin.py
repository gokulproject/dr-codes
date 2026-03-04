# b2bi/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .admin_site import b2bi_admin_site
from .models import B2BIUser, B2BIGroup
from .forms import B2BIUserCreationForm, B2BIUserChangeForm, B2BIGroupForm


# ══════════════════════════════════════════════════════════════════════════════
# B2BI USER ADMIN
# ══════════════════════════════════════════════════════════════════════════════

class B2BIUserAdmin(UserAdmin):

    # ── Forms ──────────────────────────────────────────────────────────────────
    add_form = B2BIUserCreationForm
    form     = B2BIUserChangeForm
    model    = B2BIUser

    # ── List View ──────────────────────────────────────────────────────────────
    list_display = [
        "username",
        "get_full_name",
        "is_active_badge",
        "is_staff_badge",
        "is_superuser_badge",
        "group_list",
        "date_joined",
    ]
    list_display_links = ["username", "get_full_name"]
    list_filter        = ["is_active", "is_staff", "is_superuser", "b2bi_groups", "date_joined"]
    search_fields      = ["username", "first_name", "last_name"]
    ordering           = ["-date_joined"]
    list_per_page      = 25
    date_hierarchy     = "date_joined"
    filter_horizontal  = ("b2bi_groups",)

    # ── Coloured Badges ────────────────────────────────────────────────────────
    @admin.display(description="Active", ordering="is_active")
    def is_active_badge(self, obj):
        color = "#28a745" if obj.is_active else "#dc3545"
        label = "Yes"     if obj.is_active else "No"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>', color, label
        )

    @admin.display(description="Staff", ordering="is_staff")
    def is_staff_badge(self, obj):
        color = "#007bff" if obj.is_staff else "#6c757d"
        label = "Yes"     if obj.is_staff else "No"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>', color, label
        )

    @admin.display(description="Superuser", ordering="is_superuser")
    def is_superuser_badge(self, obj):
        color = "#fd7e14" if obj.is_superuser else "#6c757d"
        label = "Yes"     if obj.is_superuser else "No"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>', color, label
        )

    @admin.display(description="Groups")
    def group_list(self, obj):
        groups = obj.b2bi_groups.all()
        if not groups:
            return format_html('<span style="color:#aaa;">—</span>')
        badges = " ".join(
            f'<span style="background:#e9ecef; padding:2px 8px; border-radius:10px; '
            f'font-size:11px;">{g.name}</span>'
            for g in groups
        )
        return format_html(badges)

    # ── CHANGE User form layout ────────────────────────────────────────────────
    fieldsets = (
        (_("Login Credentials"), {
            "fields": ("username", "password"),
        }),
        (_("Personal Information"), {
            "fields": ("first_name", "last_name"),
        }),
        (_("Permissions & Access"), {
            "fields": ("is_active", "is_staff", "is_superuser"),
            "description": (
                "<b>is_staff</b> → Can login to /b2bi-admin/ &nbsp;|&nbsp; "
                "<b>is_superuser</b> → Full access with no restrictions"
            ),
        }),
        (_("B2BI Groups"), {
            "fields": ("b2bi_groups",),
        }),
        (_("Important Dates"), {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("last_login", "date_joined")

    # ── ADD New User form layout ───────────────────────────────────────────────
    add_fieldsets = (
        (_("Account Credentials"), {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
        (_("Personal Information"), {
            "classes": ("wide",),
            "fields": ("first_name", "last_name"),
        }),
        (_("Permissions & Access"), {
            "classes": ("wide",),
            "fields": ("is_active", "is_staff", "is_superuser"),
        }),
        (_("B2BI Groups"), {
            "classes": ("wide",),
            "fields": ("b2bi_groups",),
        }),
    )

    # ── Bulk Actions ───────────────────────────────────────────────────────────
    actions = ["activate_users", "deactivate_users", "make_staff", "remove_staff"]

    @admin.action(description="✅ Activate selected users")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated successfully.")

    @admin.action(description="🚫 Deactivate selected users")
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.")

    @admin.action(description="🔑 Grant staff access")
    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f"{updated} user(s) granted staff access.")

    @admin.action(description="🔒 Remove staff access")
    def remove_staff(self, request, queryset):
        updated = queryset.update(is_staff=False)
        self.message_user(request, f"{updated} user(s) staff access removed.")

    # ── ✅ FIX — Bypass admin log FK constraint error ──────────────────────────
    def log_addition(self, request, obj, message):
        pass

    def log_change(self, request, obj, message):
        pass

    def log_deletion(self, request, obj, object_repr):
        pass


# ══════════════════════════════════════════════════════════════════════════════
# B2BI GROUP ADMIN
# ══════════════════════════════════════════════════════════════════════════════

class B2BIGroupAdmin(admin.ModelAdmin):

    # ── Forms ──────────────────────────────────────────────────────────────────
    form  = B2BIGroupForm
    model = B2BIGroup

    # ── List View ──────────────────────────────────────────────────────────────
    list_display  = ["name", "description", "user_count", "created_at", "updated_at"]
    list_filter   = ["created_at"]
    search_fields = ["name", "description"]
    ordering      = ["name"]
    list_per_page = 25

    @admin.display(description="Total Users")
    def user_count(self, obj):
        count = obj.users.count()
        color = "#28a745" if count > 0 else "#aaa"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>', color, count
        )

    # ── CHANGE Group form layout ───────────────────────────────────────────────
    fieldsets = (
        (_("Group Details"), {
            "fields": ("name", "description"),
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    # ── ADD Group form layout ──────────────────────────────────────────────────
    add_fieldsets = (
        (_("New Group"), {
            "classes": ("wide",),
            "fields": ("name", "description"),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return self.fieldsets

    # ── Bulk Actions ───────────────────────────────────────────────────────────
    actions = ["delete_selected"]

    # ── ✅ FIX — Bypass admin log FK constraint error ──────────────────────────
    def log_addition(self, request, obj, message):
        pass

    def log_change(self, request, obj, message):
        pass

    def log_deletion(self, request, obj, object_repr):
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Register on b2bi_admin_site ONLY
# ──────────────────────────────────────────────────────────────────────────────
b2bi_admin_site.register(B2BIUser,  B2BIUserAdmin)
b2bi_admin_site.register(B2BIGroup, B2BIGroupAdmin)