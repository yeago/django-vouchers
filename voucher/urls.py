from django.conf.urls.defaults import patterns, url
from .views import VoucherList, claimvoucher

urlpatterns = patterns('',
    #url(r'^$', VoucherList.as_view(), name="voucher_list"),
    url(r'(?P<voucher>[-\w]+)/claim/$', 'voucher.views.claimvoucher', name='claim_voucher'),
)
