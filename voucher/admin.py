import datetime

from django.contrib import admin
from .forms import VoucherAdminForm
from .models import Voucher


def generate_token(self, request, queryset):
    for voucher in queryset.all():
        voucher.generate_token()


def deactivate_token(self, request, queryset):
    for voucher in queryset.all():
        voucher.activated = False
        voucher.save()


def activate_token(self, request, queryset):
    for voucher in queryset.all():
        voucher.activated = True
        voucher.save()


class VoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher', 'user', 'activated', 'notified', 'claimed_date', 'created_by', 'last_editor']
    readonly_fields = ['creation_date', 'claimed_date', 'activated', 'voucher_info', 'created_by', 'last_editor',
                       'last_edit_datetime', 'notified']
    actions = [generate_token, deactivate_token]
    form = VoucherAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(VoucherAdmin, self).get_form(request, obj=obj, **kwargs)
        if obj:
            obj.last_editor = request.user
            obj.save()
        if not obj:
            form.creator = request.user
        return form

    def save_model(self, request, obj, form, change):
        if obj and not obj.pk:
            obj.created_by = request.user
        obj.last_editor = request.user
        obj.last_edit_datetime = datetime.datetime.now()
        super(VoucherAdmin, self).save_model(request, obj, form, change)


admin.site.register(Voucher, VoucherAdmin)
