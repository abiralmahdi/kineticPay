from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .decorators import active_subscription_required

from .models import (
    Merchant,
    SubscriptionPlan,
    MerchantSubscription
)

from home.utils.whatsapp import send_whatsapp_message
from home.models import NotificationLog


def merchant_register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        business_name = request.POST.get("business_name")
        slug = request.POST.get("slug")

        whatsapp_number = request.POST.get("whatsapp_number")
        mfs_payment_number = request.POST.get("mfs_payment_number")

        # Check username
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("merchant_register")

        # Check email
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("merchant_register")

        # Check slug
        if Merchant.objects.filter(slug=slug).exists():
            messages.error(request, "Business slug already exists.")
            return redirect("merchant_register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Merchant.objects.create(
            user=user,
            business_name=business_name,
            slug=slug,
            whatsapp_number=whatsapp_number,
            mfs_payment_number=mfs_payment_number
        )

        messages.success(
            request,
            "Registration successful. Please choose a subscription plan."
        )

        login(request, user)
        return redirect("select_subscription")

    return render(
        request,
        "register.html"
    )

def merchant_login(request):

    if request.user.is_authenticated:
        return redirect("merchant_dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            merchant = getattr(
                user,
                "merchant_profile",
                None
            )

            if merchant:

                active_subscription = MerchantSubscription.objects.filter(
                    merchant=merchant,
                    status="active",
                    end_date__gt=timezone.now()
                ).exists()

                if not active_subscription:
                    return redirect("select_subscription")

            return redirect("merchant_dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "login.html"
    )

@login_required
def merchant_logout(request):

    logout(request)

    messages.success(
        request,
        "Logged out successfully."
    )

    return redirect("merchant_login")



from django.contrib.auth.decorators import login_required
from django.utils import timezone
from home.models import Order, VerifiedTransactionCache

from .decorators import active_subscription_required
from .models import MerchantSubscription

@login_required
@active_subscription_required
def merchant_dashboard(request):

    merchant = request.user.merchant_profile

    active_subscription = MerchantSubscription.objects.filter(
        merchant=merchant,
        status="active",
        end_date__gt=timezone.now()
    ).first()

    # Order counts

    pending_stock_count = Order.objects.filter(
        merchant=merchant,
        order_status='awaiting_stock_check'
    ).count()

    awaiting_payment_count = Order.objects.filter(
        merchant=merchant,
        order_status='approved_awaiting_payment'
    ).count()

    ready_to_ship_count = Order.objects.filter(
        merchant=merchant,
        order_status='paid_ready_to_ship'
    ).count()

    # Current month orders

    month_start = timezone.now().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    total_orders_this_month = Order.objects.filter(
        merchant=merchant,
        created_at__gte=month_start
    ).count()

    # Recent orders

    recent_orders = Order.objects.filter(
        merchant=merchant
    ).order_by('-created_at')[:10]

    # Subscription usage

    if active_subscription.plan.max_orders_per_month > 0:

        usage_percentage = min(
            (
                total_orders_this_month /
                active_subscription.plan.max_orders_per_month
            ) * 100,
            100
        )

    else:
        usage_percentage = 0

    # Remaining subscription days

    days_remaining = (
        active_subscription.end_date.date() -
        timezone.now().date()
    ).days

    # Cached transactions

    cached_transactions = VerifiedTransactionCache.objects.filter(
        merchant=merchant
    ).count()

    context = {

        "merchant": merchant,
        "subscription": active_subscription,

        "pending_stock_count": pending_stock_count,
        "awaiting_payment_count": awaiting_payment_count,
        "ready_to_ship_count": ready_to_ship_count,
        "total_orders_this_month": total_orders_this_month,

        "recent_orders": recent_orders,

        "usage_percentage": usage_percentage,
        "days_remaining": days_remaining,

        "cached_transactions": cached_transactions,
        "sms_sync_enabled": True,  # temporary placeholder
    }

    return render(
        request,
        "dashboard.html",
        context
    )


@login_required
def select_subscription(request):

    merchant = request.user.merchant_profile

    plans = SubscriptionPlan.objects.all()

    if request.method == "POST":

        plan_id = request.POST.get("plan_id")

        plan = get_object_or_404(
            SubscriptionPlan,
            id=plan_id
        )

        MerchantSubscription.objects.filter(
            merchant=merchant,
            status="active"
        ).update(
            status="expired"
        )

        billing_cycle = request.POST.get("billing_cycle")

        if billing_cycle == "yearly":
            end_date = timezone.now() + timedelta(days=365)
        else:
            end_date = timezone.now() + timedelta(days=30)

        MerchantSubscription.objects.create(
            merchant=merchant,
            plan=plan,
            status="active",
            start_date=timezone.now(),
            end_date=end_date
        )


        messages.success(
            request,
            "Subscription activated successfully."
        )

        return redirect("merchant_dashboard")

    active_subscription = MerchantSubscription.objects.filter(
        merchant=merchant,
        status='active',
        end_date__gt=timezone.now()
    ).first()
    
    return render(
        request,
        "select_subscription.html",
        {
            "plans": plans,
            "active_subscription": active_subscription
        }
    )


from home.models import Order
from django.db.models import Q
from datetime import datetime
from django.utils import timezone

@login_required
@active_subscription_required
def orders(request):

    merchant = request.user.merchant_profile

    orders = Order.objects.filter(
        merchant=merchant
    ).order_by('-created_at')

    search = request.GET.get('search')
    status = request.GET.get('status')
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if search:
        orders = orders.filter(
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search) |
            Q(id__icontains=search)
        )

    if status:
        orders = orders.filter(
            order_status=status
        )
    if start_date:

        orders = orders.filter(
            created_at__date__gte=start_date
        )

    if end_date:

        orders = orders.filter(
            created_at__date__lte=end_date
        )


    context = {

        "orders": orders,

        "search": search or "",

        "selected_status": status or "",

        "start_datetime": start_date or "",

        "end_datetime": end_date or "",
    }

    return render(
        request,
        "orders.html",
        context
    )


# merchants/views.py

from django.shortcuts import render
from django.shortcuts import get_object_or_404

from home.models import Order


@login_required
@active_subscription_required
def order_details(request, order_id):

    merchant = request.user.merchant_profile

    order = get_object_or_404(
        Order,
        id=order_id,
        merchant=merchant
    )

    context = {
        "order": order
    }

    return render(
        request,
        "order_details.html",
        context
    )





import secrets

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils import timezone

from home.models import Order


@login_required
@active_subscription_required
def approve_order(
    request,
    order_id
):

    if request.method != "POST":
        return redirect(
            "merchant_orders"
        )

    merchant = request.user.merchant_profile

    order = get_object_or_404(
        Order,
        id=order_id,
        merchant=merchant
    )

    amount = request.POST.get(
        "total_amount"
    )

    token = secrets.token_urlsafe(32)

    order.total_amount = amount

    order.order_status = (
        "approved_awaiting_payment"
    )

    order.payment_link_token = token

    order.payment_link_expires_at = (
        timezone.now()
        + timedelta(hours=2)
    )

    order.approved_at = timezone.now()

    order.save()


    message = f"""Your order has been approved.\nAmount: ৳{order.total_amount}\nPlease complete payment.\nPayment Link:\nhttps://kineticpay.com/pay/{order.payment_link_token}/"""

    send_whatsapp_message(

            order.customer_phone,

            message
    )

    print("Message sent")

    NotificationLog(order=order, channel="WhatsApp", recipient=order.customer_phone, message=message).save()

    messages.success(
        request,
        "Order approved and payment link sent."
    )

    return redirect(
        "order_details",
        order_id=order.id
    )


@login_required
@active_subscription_required
def reject_order(
    request,
    order_id
):

    if request.method != "POST":
        return redirect(
            "merchant_orders"
        )

    merchant = request.user.merchant_profile

    order = get_object_or_404(
        Order,
        id=order_id,
        merchant=merchant
    )

    order.order_status = "cancelled"

    order.save()
    message = f"""Hello {order.customer_name},\n\nUnfortunately the item(s) you requested are currently out of stock.\nPlease contact us again for updated availability.\nThank you."""
    send_whatsapp_message(

        order.customer_phone,
        message
        
    )

    NotificationLog(order=order, channel="WhatsApp", recipient=order.customer_phone, message=message).save()


    messages.success(
        request,
        "Order cancelled and customer notified."
    )

    return redirect(
        "order_details",
        order_id=order.id
    )