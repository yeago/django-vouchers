from django.conf.urls import url
from voucher import views

urlpatterns = [
    url(r'claim/$', views.claim_voucher, name='claim_voucher'),
    url(r'claim/(?P<human_token>[-\w]+)$', views.claim_voucher, name='claim_voucher'),
]
