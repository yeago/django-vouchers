import datetime
from jsonfield.fields import JSONField
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy
from django.db import models

from voucher.humanhash import HumanHasher

from voucher.utils import get_voucher_forms, render_email_for_voucher_claimed, get_voucher_form


VOUCHER_SEND_NOTIFICATION = getattr(settings, 'VOUCHER_SEND_NOTIFICATION', True)
NOTIFY_VOUCHER_FROM = getattr(settings, 'NOTIFY_VOUCHER_FROM', None)
VOUCHER_MANAGERS = getattr(settings, 'VOUCHER_MANAGERS', [])

VOUCHERS = get_voucher_forms()


def get_voucher_choices():
    return [(s_name, voucher['name']) for s_name, voucher in VOUCHERS.items()]


class Voucher(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Creation Date'))
    claimed_date = models.DateTimeField(verbose_name=gettext_lazy('Used Date'), blank=True, null=True)
    expiry_date = models.DateTimeField(verbose_name=gettext_lazy('Expiration Date'), blank=True, null=True)
    voucher = models.CharField(choices=get_voucher_choices(), max_length=50)
    voucher_info = JSONField(blank=True, null=True)
    token = models.CharField(unique=True, db_index=True, max_length=50)
    human_token = models.CharField(unique=True, db_index=True, max_length=255)
    user = models.ForeignKey(User, blank=True, null=True, related_name='vouchers', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, verbose_name=gettext_lazy('Created By'), blank=True, null=True,
                                   related_name='my_vouchers', on_delete=models.CASCADE)
    last_edit_datetime = models.DateTimeField(auto_now=True, blank=True, null=True)
    last_editor = models.ForeignKey(User, verbose_name=gettext_lazy('Last Editor'), blank=True, null=True,
                                    related_name='edited_vouchers', on_delete=models.SET_NULL)
    notified = models.BooleanField(default=False)
    activated = models.BooleanField(default=True)

    def generate_token(self):
        human_hasher = HumanHasher()
        return human_hasher.uuid()

    def reactivate_voucher(self):
        self.human_token, self.token = self.generate_token()
        self.activated = True
        self.claimed_date = None
        self.notified = False
        return self.human_token, self.token

    def is_valid_token(self, token):
        human_hasher = HumanHasher()
        return human_hasher.humanize(token) == self.human_token

    def is_claimed(self):
        return bool(self.user and self.claimed_date and not self.activated and self.voucher)

    def assign_voucher(self, user):
        if self.user:
            raise ValidationError("Cannot assign voucher, already taken.")

        if not self.is_claimed():
            self.user = user
            self.save()

    def claim_voucher(self, user, human_token, voucher_info=None):
        if self.is_claimed():
            raise ValidationError("Voucher already claimed by %s" % self.user)

        if not slugify(self.voucher) in VOUCHERS:
            raise ValidationError("Invalid voucher choice.")

        voucher_form = get_voucher_form(self)(voucher_info or {})
        if not voucher_form.is_valid():
            raise ValidationError("Invalid voucher info.")

        if human_token != self.human_token:
            raise ValidationError("Cannot claim voucher, invalid token.")

        if not isinstance(user, User):
            user = get_object_or_404(User, username=user)

        if not self.user:
            self.user = user
        elif self.user and user != self.user:
            raise ValidationError("Cannot claim voucher, the user assigned don't match")

        self.voucher_info = voucher_form.cleaned_data
        self.claimed_date = datetime.datetime.now()
        self.activated = False
        self.notified = False
        self.save()

    def get_voucher_form(self, voucher_info=None):
        voucher_info = voucher_info or self.voucher_info or {}
        if self.voucher and self.voucher in VOUCHERS:
            form = get_voucher_form(self)(voucher_info)
            form.is_valid()
            return form

    def get_voucher_info_template(self):
        if self.voucher_info and self.voucher:
            voucher_form = get_voucher_form(self)
            for field in voucher_form.base_fields:
                voucher_form.base_fields[field].widget.attrs['readonly'] = True
            voucher_form = voucher_form(self.voucher_info)
            if voucher_form.is_valid():
                return voucher_form.as_table()
        return ''

    def save(self, *args, **kwargs):
        self.voucher = slugify(self.voucher)
        if not self.voucher in VOUCHERS:
            raise ValueError("Cannot create voucher, invalid voucher choice... (%s)" % self.voucher)
        if not self.token:
            for n_try in range(11):
                if n_try == 10:
                    raise ValidationError("Cannot create voucher, max attempts reached.")
                human_token, token = self.generate_token()
                try:
                    Voucher.objects.get(human_token=human_token, token=token)
                    Voucher.objects.create()
                except Voucher.DoesNotExist:
                    self.human_token = human_token
                    self.token = token
                    break
        elif VOUCHER_SEND_NOTIFICATION and self.is_claimed() and not self.notified:
            if not NOTIFY_VOUCHER_FROM:
                raise ValidationError("You must define a sender in your settings.py NOTIFY_VOUCHER_FROM")
            self.notified = True
            subject = "Voucher claimed (%s) by %s" % (self.voucher, self.user)
            from_email, to = NOTIFY_VOUCHER_FROM, [i for (_, i) in VOUCHER_MANAGERS]
            html_content = render_email_for_voucher_claimed(self)
            msg = EmailMultiAlternatives(subject, subject, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
        super(Voucher, self).save(*args, **kwargs)
