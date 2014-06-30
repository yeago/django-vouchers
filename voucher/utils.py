import importlib

from django.conf import settings


def get_voucher_forms(prefix=None):
    voucher_forms = {} # Here we store our voucher forms
    for voucher_name, modstring in settings.VOUCHERS:
        modstring = modstring.split('.')
        klass = modstring.pop()
        package = ".".join(modstring)
        module = importlib.import_module(package)
        voucher_form = getattr(module, klass)()
        voucher_form.name = voucher_name
        voucher_forms[voucher_name] = voucher_form
    return voucher_forms
