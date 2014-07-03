import datetime

from django.contrib import admin
from voucher.forms import VoucherAdminForm
from voucher.models import Voucher


def generate_token(self, request, queryset):
    for voucher in queryset.all():
        voucher.generate_token()


def deactivate_token(self, request, queryset):
    for voucher in queryset.all():
        voucher.activated = False
        voucher.save()


def reactivate_token(self, request, queryset):
    max_tries = 5
    for voucher in queryset.all():
        tries = 0
        while tries < max_tries:
            voucher.reactivate_voucher()
            try:
                obj = Voucher.objects.get(human_token=voucher.human_token)
                if voucher.pk != obj.pk:
                    tries += 1
                else:
                    break
            except Voucher.MultipleObjectsReturned:
                # This never should happen since there is a Unique constraint for this field, but lets be more safety.
                tries += 1
            except Voucher.DoesNotExist:
                break
        voucher.save()


class VoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher', 'user', 'activated', 'notified', 'claimed_date', 'created_by', 'last_editor']
    readonly_fields = ['creation_date', 'claimed_date', 'activated', 'voucher_info', 'created_by', 'last_editor',
                       'last_edit_datetime', 'notified']
    actions = [generate_token, deactivate_token, reactivate_token]
    form = VoucherAdminForm
    fieldsets = (('Voucher Info', {'fields': ['voucher', 'token', 'human_token', 'expiry_date', 'user', 'claimed_date']}),
                 ('Edition', {'fields': ['created_by', 'creation_date', 'last_editor', 'last_edit_datetime']}),
                 ('Status', {'fields': ['notified', 'activated']}))

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
