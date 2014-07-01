from django import forms
from .humanhash import HumanHasher

from .models import Voucher


class VoucherAdminForm(forms.ModelForm):

    class Meta:
        model = Voucher

    def __init__(self, *args, **kwargs):
        super(VoucherAdminForm, self).__init__(*args, **kwargs)
        human_token, token = self.generate_token()
        self.fields['human_token'].initial = human_token
        self.fields['token'].initial = token
        self.fields['human_token'].widget.attrs['readonly'] = True
        self.fields['token'].widget.attrs['readonly'] = True

    def generate_token(self):
        human_hasher = HumanHasher()
        return human_hasher.uuid()


class BaseVoucherForm(forms.Form):
    token = forms.CharField(max_length=50)
