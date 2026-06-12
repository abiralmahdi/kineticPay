from functools import wraps

from django.shortcuts import redirect
from django.utils import timezone

from home.models import Order
from .models import MerchantSubscription


def active_subscription_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        merchant = request.user.merchant_profile

        subscription = MerchantSubscription.objects.filter(
            merchant=merchant,
            status="active",
            end_date__gt=timezone.now()
        ).select_related("plan").first()

        if not subscription:
            return redirect("select_subscription")

        if not subscription.plan.unlimited:

            order_count = Order.objects.filter(
                merchant=merchant,
                created_at__gte=subscription.start_date,
                created_at__lte=subscription.end_date
            ).count()

            if order_count >= subscription.plan.max_orders_per_month:

                subscription.status = "expired"
                subscription.save(update_fields=["status"])

                return redirect("select_subscription")

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper