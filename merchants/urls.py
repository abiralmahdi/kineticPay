from django.urls import path

from . import views

urlpatterns = [

    path(
        "register/",
        views.merchant_register,
        name="merchant_register"
    ),

    path(
        "login/",
        views.merchant_login,
        name="merchant_login"
    ),

    path(
        "logout/",
        views.merchant_logout,
        name="merchant_logout"
    ),

    path(
        "dashboard/",
        views.merchant_dashboard,
        name="merchant_dashboard"
    ),

    path(
        "subscription/",
        views.select_subscription,
        name="select_subscription"
    ),
    path(
        "orders/",
        views.orders,
        name="merchant_orders"
    ),
    # merchants/urls.py

    path(
        "orders/<int:order_id>/",
        views.order_details,
        name="order_details"
    ),

    path(
        "orders/<int:order_id>/approve/",
        views.approve_order,
        name="approve_order"
    ),

    path(
        "orders/<int:order_id>/reject/",
        views.reject_order,
        name="reject_order"
    ),
]