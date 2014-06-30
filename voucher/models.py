import datetime
from jsonfield.fields import JSONField

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy
from django.db import models

from .humanhash import HumanHasher

from .utils import get_voucher_forms


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
                                   related_name=None)
    activated = models.BooleanField(default=True)

    def generate_token(self):
        human_hasher = HumanHasher()
        human_token, token = human_hasher.uuid()
        self.token = token
        self.human_token = human_token
        self.activated = True
        self.save()
        return human_token, token

    def is_valid_token(self, token):
        human_hasher = HumanHasher()
        return human_hasher.humanize(token) == self.human_token

    def claim_voucher(self, user, voucher_info=None, notify_user=False):
        if not isinstance(user, User):
            user = get_object_or_404(User, user)
        self.user = user
        self.claimed_date = datetime.datetime.now()
        self.activated = False
        self.voucher_info = voucher_info
        self._send_notifications(notify_user=notify_user)
        self.save()

    def _send_notifications(self, notify_user=False):
        voucher_info = self.get_voucher_info_template()
        pass

    def get_voucher_info_template(self):
        if self.voucher_info and self.voucher:
            voucher_form = VOUCHERS[self.voucher](self.voucher_info)
            if voucher_form.is_valid():
                return voucher_form.as_table()
        return ''

    def save(self, *args, **kwargs):
        import ipdb; ipdb.set_trace()
        super(Voucher, self).save(*args, **kwargs)
