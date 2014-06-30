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
    list_display = ['voucher', 'user', 'activated', 'claimed_date', 'created_by']
    readonly_fields = ['creation_date', 'claimed_date', 'activated', 'voucher_info', 'created_by']
    actions = [generate_token, deactivate_token]
    form = VoucherAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(VoucherAdmin, self).get_form(request, obj=obj, **kwargs)
        import ipdb; ipdb.set_trace()
        form.current_user = request.user
        return form

admin.site.register(Voucher, VoucherAdmin)
