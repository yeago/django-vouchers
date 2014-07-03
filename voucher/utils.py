import importlib

from django.template.loader import render_to_string
from django.conf import settings


def get_voucher_forms(prefix=None):
    voucher_forms = {} # Here we store our voucher forms
    for voucher_name, modstring in settings.VOUCHERS:
        modstring = modstring.split('.')
        klass = modstring.pop()
        package = ".".join(modstring)
        module = importlib.import_module(package)
        voucher_form = getattr(module, klass)
        voucher_forms[voucher_name] = voucher_form
    return voucher_forms


def get_voucher_form(voucher):
    vouchers_forms = get_voucher_forms()
    return vouchers_forms.get(voucher.voucher)


def render_email_for_voucher_claimed(voucher):
    return render_to_string('notify.html', {'voucher': voucher})
