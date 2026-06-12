from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.redirect_to_dashboard,
        name="redirect_to_dashboard"
    ),
    path(
        "accounts/login/",
        views.redirect_to_login,
        name="redirect_to_login"
    ),
    path(
        "order-success/<int:order_id>/",
        views.order_success,
        name="order_success"
    ),

    path(
        "pay/<str:token>/",
        views.payment_page,
        name="payment_page"
    ),

    path(
        "pay/<str:token>/submit",
        views.submit_payment,
        name="submit_payment"
    ),

    path(
        "api/sms-webhook/",
        views.sms_webhook,
        name="sms_webhook"
    ),
    path(
        "<slug:merchant_slug>/",
        views.order_form,
        name="order_form"
    ),
]
