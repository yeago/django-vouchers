import datetime

from django.contrib import admin, messages
from voucher.forms import VoucherAdminForm
from voucher.models import Voucher, NOTIFY_VOUCHER_FROM
from voucher.utils import get_notify_user_template, email


def notify_users_to_claim(self, request, queryset):
    cannot_notify_users = []
    for voucher in queryset.all():
        if voucher.user and voucher.activated:
            try:
                html_content = get_notify_user_template(voucher)
                subject = "Hi %s! You have a voucher to claim in TappeOut.net!" % voucher.user.username
                from_email, to = NOTIFY_VOUCHER_FROM, voucher.user.email
                email(subject, from_email, [to], html_content)
            except Exception as e:
                cannot_notify_users.append(voucher.user.username)
                messages.error(request, '(pk=%s): %s (%s)' % (voucher.user.username, e.message, type(e)))
        elif not voucher.user:
            cannot_notify_users.append(voucher.user.username)
            messages.warning(request, "(pk=%s) Voucher not assigned to any user!" % voucher.pk)
        elif not voucher.activated:
            cannot_notify_users.append(voucher.user.username)
            messages.warning(request, "(pk=%s) Voucher not activated!" % voucher.pk)
    if not cannot_notify_users:
        messages.success(request, 'Users have been notified')


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
    raw_id_fields = ['user']
    list_display = ['voucher', 'user', 'activated', 'notified', 'claimed_date',
                    'created_by', 'last_editor', 'human_token']
    readonly_fields = ['creation_date', 'claimed_date', 'activated', 'voucher_info', 'created_by', 'last_editor',
                       'last_edit_datetime', 'notified']
    actions = [notify_users_to_claim, generate_token, deactivate_token, reactivate_token]
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
