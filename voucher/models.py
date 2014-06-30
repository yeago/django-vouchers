import datetime
from jsonfield.fields import JSONField

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy
from django.db import models

from .humanhash import HumanHasher

from .utils import get_voucher_forms


VOUCHER_SEND_NOTIFICATION = getattr(settings, 'VOUCHER_SEND_NOTIFICATION', True)
NOTIFY_VOUCHER_FROM = getattr(settings, 'NOTIFY_VOUCHER_FROM', None)
SEND_TO = getattr(settings, 'VOUCHER_MANAGERS', ['fmc0208@gmail.com'])

VOUCHERS = get_voucher_forms()


def get_voucher_choices():
    return [(voucher, voucher.upper()) for voucher in VOUCHERS.keys()]


class Voucher(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=ugettext_lazy('Creation Date'))
    claimed_date = models.DateTimeField(verbose_name=ugettext_lazy('Used Date'), blank=True, null=True)
    expiry_date = models.DateTimeField(verbose_name=ugettext_lazy('Expiration Date'), blank=True, null=True)
    voucher = models.CharField(choices=get_voucher_choices(), max_length=50)
    voucher_info = JSONField(blank=True, null=True)
    token = models.CharField(max_length=50)
    human_token = models.CharField(max_length=255)
    user = models.ForeignKey(User, blank=True, null=True, related_name='vouchers')
    created_by = models.ForeignKey(User, verbose_name=ugettext_lazy('Created By'), blank=True, null=True,
                                   related_name='my_vouchers')
    last_edit_datetime = models.DateTimeField(auto_now=True, blank=True, null=True)
    last_editor = models.ForeignKey(User, verbose_name=ugettext_lazy('Last Editor'), blank=True, null=True,
                                   related_name='edited_vouchers')
    notified = models.BooleanField(default=False)
    activated = models.BooleanField(default=True)

    def generate_token(self):
        human_hasher = HumanHasher()
        human_token, token = human_hasher.uuid()
        self.token = token
        self.human_token = human_token
        self.activated = True
        return human_token, token

    def is_valid_token(self, token):
        human_hasher = HumanHasher()
        return human_hasher.humanize(token) == self.human_token

    def is_claimed(self):
        return bool(self.user and self.claimed_date and not self.activated and self.voucher)

    def assign_voucher(self, user):
        if self.user:
            raise ValueError("Cannot assign voucher, already taken.")

        if not self.is_claimed():
            self.user = user
            self.save()

    def claim_voucher(self, user, human_token, voucher_info=None):
        if self.is_claimed():
            raise ValueError("Voucher already claimed by %s" % self.user)
        if human_token != self.human_token:
            raise ValueError("Cannot claim voucher, invalid token.")
        if self.voucher and not VOUCHERS[self.voucher](voucher_info or {}).is_valid():
            raise ValueError("Invalid voucher info.")

        if not isinstance(user, User):
            user = get_object_or_404(User, username=user)

        if self.user and user != self.user:
            raise ValueError("Cannot claim voucher, the user assigned don't match")
        elif not self.user:
            self.user = user
        self.voucher_info = voucher_info
        self.claimed_date = datetime.datetime.now()
        self.activated = False
        self.notified = True
        self.save()

    def get_voucher_info_template(self):
        if self.voucher_info and self.voucher:
            voucher_form = VOUCHERS[self.voucher]
            for field in voucher_form.base_fields:
                voucher_form.base_fields[field].widget.attrs['readonly'] = True
            voucher_form = voucher_form(self.voucher_info)
            if voucher_form.is_valid():
                return voucher_form.as_table()
        return ''

    def save(self, *args, **kwargs):
        if not self.token:
            self.generate_token()
        if VOUCHER_SEND_NOTIFICATION and self.is_claimed() and not self.notified:
            if not NOTIFY_VOUCHER_FROM:
                raise ValueError("You must define a sender in your settings.py NOTIFY_VOUCHER_FROM")
            subject, from_email, to = "Voucher claimed (%s)" % self.voucher, NOTIFY_VOUCHER_FROM, SEND_TO
            text_content = 'The user %s has claimed the voucher %s (%s)' % (self.user, self.voucher, self.human_token)
            html_content = self.get_voucher_info_template()
            msg = EmailMultiAlternatives(subject, text_content, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
        super(Voucher, self).save(*args, **kwargs)
