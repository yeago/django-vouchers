import importlib
from django.template.loader import select_template
from django.template.defaultfilters import slugify
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
        voucher_forms[slugify(voucher_name)] = {'form_class': voucher_form,
                                                'name': voucher_name}
    return voucher_forms


def get_voucher_form(voucher):
    vouchers_forms = get_voucher_forms()
    return vouchers_forms.get(slugify(voucher.voucher), {}).get('form_class')


def get_voucher_form_name(voucher):
    vouchers_forms = get_voucher_forms()
    return vouchers_forms.get(slugify(voucher.voucher), {}).get('name')


def get_voucher_template(voucher=None):
    try_templates = [slugify(voucher.voucher) if voucher else 'voucher',
                     voucher.voucher if voucher else 'voucher',
                     'voucher']
    return select_template(['voucher/%s.html' % voucher for voucher in try_templates])


def render_email_for_voucher_claimed(voucher):
    return render_to_string('notify.html', {'voucher': voucher})
