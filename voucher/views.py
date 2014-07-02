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
            self.f = Voucher.objects.all()
        except Voucher.DoesNotExist:
            raise Http404
        return self.f

    def get_context_data(self, **kwargs):
        context = super(VoucherList, self).get_context_data(**kwargs)
        context.update({'vouchers': self.get_queryset()})
        return context


def claimvoucher(request, voucher):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('%s?next=%s' % (LOGIN_URL, request.path))
    voucher = get_object_or_404(Voucher, id=voucher)
    if voucher.user != request.user:
        raise Http404()
    if request.method == 'POST' and 'submit' in request.POST and 'Claim Voucher' in request.POST['submit']:
        token = request.POST.get('token')
        voucher_info = request.POST
        try:
            voucher.claim_voucher(request.user, token, voucher_info=voucher_info)
        except ValueError as error:
            messages.error(request, error.message)
            return render_to_response('voucher/voucher.html', RequestContext(request))
        messages.info(request, 'Voucher claimed!')
        return render_to_response('voucher/voucher.html', RequestContext(request))
    elif request.method == 'GET':
        form = voucher.get_voucher_form()
        return render_to_response('voucher/voucher.html',
                                  RequestContext(request, {'is_claimed': voucher.is_claimed(),
                                                           'form': form,
                                                           'voucher': voucher}))
