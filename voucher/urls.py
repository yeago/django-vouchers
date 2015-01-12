try:
    from django.conf.urls.defaults import patterns, url  # Django 1.4
except Exception as e:
    from django.conf.urls import patterns, url  # Django 1.6

urlpatterns = patterns('',
    #url(r'^$', VoucherList.as_view(), name="voucher_list"),
    url(r'claim/$', 'voucher.views.claim_voucher', name='claim_voucher'),
    url(r'claim/(?P<human_token>[-\w]+)$', 'voucher.views.claim_voucher', name='claim_voucher'),
)
