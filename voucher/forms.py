from django import forms
from voucher.humanhash import HumanHasher

from voucher.models import Voucher


class VoucherAdminForm(forms.ModelForm):
    class Meta:
        model = Voucher

    def __init__(self, *args, **kwargs):
        super(VoucherAdminForm, self).__init__(*args, **kwargs)
        token, human_token = self.generate_token()
        self.fields['token'].initial = token
        self.fields['token'].widget.attrs['readonly'] = True

        self.fields['human_token'].initial = human_token
        self.fields['human_token'].widget.attrs['readonly'] = True

    def generate_token(self):
        max_tries, tries = 5, 0
        while tries <= max_tries:
            human_hasher = HumanHasher()
            human_token, token = human_hasher.uuid()
            try:
                Voucher.objects.get(human_token=human_token)
                tries += 1
            except Voucher.DoesNotExist:
                break
        return token, human_token

    def refresh_tokens(self):
        token, human_token = self.generate_token()
        self.cleaned_data['token'] = token
        self.cleaned_data['human_token'] = human_token


class TokenForm(forms.Form):
    token = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
