from .models import Voucher

from django.contrib import messages
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.views.generic.list import ListView
from django.conf import settings

LOGIN_URL = getattr(settings, 'LOGIN_URL', '/accounts/login/')


class VoucherList(ListView):
    template_object_name = 'voucher',
    template_name = 'voucher_list.html'

    def get_queryset(self):
        try:
            self.f = Voucher.objects.filter(activated=True)
        except Voucher.DoesNotExist:
            raise Http404
        return self.f

    def get_context_data(self, **kwargs):
        context = super(VoucherList, self).get_context_data(**kwargs)
        context.update({'vouchers': self.get_queryset()})
        return context


def claimvoucher(request, voucher):
    if not request.user.is_authenticated() or not \
            ('submit' in request.POST and 'Claim Voucher' in request.POST['submit']):
        messages.error(request, 'Cannot claim voucher')
        return render_to_response('voucher_list.html', RequestContext(request))
    voucher = get_object_or_404(Voucher, id=voucher)
    token = request.POST.get('token')
    voucher_info = request.POST
    try:
        voucher.claim_voucher(request.user, token, voucher_info=voucher_info)
    except ValueError as error:
        messages.error(request, error.message)
        return render_to_response('voucher_list.html', RequestContext(request))
    messages.info(request, 'Voucher claimed!')
    return render_to_response('voucher_list.html', RequestContext(request))