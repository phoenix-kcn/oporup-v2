from django.urls import path
from . import views

urlpatterns = [
    path('checkout', views.checkout, name='checkout'),
    path('billing_info', views.billing_info, name='billing_info'),
    path('shipped_dash', views.shipped_dash, name='shipped_dash'),
    path('not_shipped_dash', views.not_shipped_dash, name='not_shipped_dash'),
    path('order/<int:pk>', views.orders, name='orders'),
    path('process_order', views.process_order, name='process_order'),
    path('payment_success_callback/', views.payment_success_callback, name='payment_success_callback'),
    path('payment_fail/', views.payment_fail, name='payment_fail'),
] 