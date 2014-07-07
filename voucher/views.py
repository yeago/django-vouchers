from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import Http404
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.exceptions import ValidationError

from voucher.forms import TokenForm
from voucher.utils import get_voucher_form, get_voucher_form_name, get_voucher_template
from voucher.models import Voucher


LOGIN_URL = getattr(settings, 'LOGIN_URL', '/accounts/login/')


@login_required(login_url=LOGIN_URL)
def claim_voucher(request, human_token=None):
    """
    /vouchers/claim/
    /vouchers/claim/<human_token>
    """
    human_token = slugify(human_token or '')
    voucher_name, voucher_image = '', ''
    is_claimed = False
    form = None
    voucher = None

    if request.method == 'GET' and human_token:
        voucher = get_object_or_404(Voucher, human_token=human_token)
        form = get_voucher_form(voucher)()
        if voucher.user and voucher.user != request.user:
            raise Http404()
        elif not voucher.user:
            voucher.user = request.user
            voucher.save()
            voucher_name = get_voucher_form_name(voucher)
            messages.success(request, "The voucher %s has been assigned to you, "
                                      "fill in the form to claim your voucher!" % voucher_name)
        is_claimed = voucher.is_claimed()

    elif request.method == 'GET' and not human_token:
        form = TokenForm()
    elif request.method == 'POST':
        token_form = TokenForm(request.POST)
        if token_form.is_valid():
            human_token = slugify(token_form.cleaned_data['token'])
            new_url = reverse('claim_voucher', args=[human_token])
            return redirect(new_url)

        if 'submit' in request.POST and 'Send' in request.POST['submit'] and human_token:
            human_token = slugify(human_token)
            voucher = get_object_or_404(Voucher, human_token=human_token, user=request.user)
            voucher_klass_form = get_voucher_form(voucher)
            voucher_name = get_voucher_form_name(voucher)
            form = voucher_klass_form(request.POST)
            is_claimed = voucher.is_claimed()
            if form.is_valid() and not is_claimed:
                try:
                    voucher.claim_voucher(request.user, human_token, form.cleaned_data)
                    messages.success(request, 'Voucher information has been sent!')
                except ValidationError as error:
                    messages.error(request, '\n'.join(error.messages))

    template = get_voucher_template(voucher)
    return render_to_response(template.name,
                              RequestContext(request, {'voucher_name': voucher_name,
                                                       'token': human_token,
                                                       'is_claimed': is_claimed,
                                                       'form': form,
                                                       'voucher': voucher}))
