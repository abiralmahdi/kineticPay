# home/views.py

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect

from merchants.models import Merchant
from .models import Order, OrderImage, NotificationLog, VerifiedTransactionCache
from .utils.whatsapp import (
    send_whatsapp_message
)
from django.shortcuts import (
    render,
    get_object_or_404
)


def redirect_to_dashboard(request):
    return redirect("/merchants/dashboard")


def redirect_to_login(request):
    return redirect("/merchants/login")

def order_form(request, merchant_slug):

    merchant = get_object_or_404(
        Merchant,
        slug=merchant_slug
    )

    if request.method == "POST":

        order = Order.objects.create(

            merchant=merchant,

            customer_name=request.POST.get(
                "customer_name"
            ),

            customer_phone=request.POST.get(
                "customer_phone"
            ),

            delivery_address=request.POST.get(
                "delivery_address"
            ),

            order_items=request.POST.get(
                "order_items"
            ),

            total_amount=0
        )

        images = request.FILES.getlist(
            "product_images"
        )

        for image in images:

            OrderImage.objects.create(
                order=order,
                image=image
            )
        
        message = f"""New Order Received \n\nCustomer: {order.customer_name}\nPhone: {order.customer_phone}\n\nItems:
            \n{order.order_items}
            \n\nOpen Dashboard: https://kineticpay.com/merchants/orders/{order.id}/
            """
        send_whatsapp_message(

                merchant.whatsapp_number,

                message
        )

        NotificationLog(order=order, channel="WhatsApp", recipient=order.customer_phone, message=message).save()

        print("Message sent")


        return redirect(
            "order_success",
            order_id=order.id
        )

    return render(
        request,
        "order_form.html",
        {
            "merchant": merchant
        }
    )


def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    return render(
        request,
        "order_success.html",
        {
            "order": order
        }
    )



from django.shortcuts import (
    render,
    get_object_or_404
)
from django.utils import timezone


def payment_page(request, token):

    order = get_object_or_404(
        Order,
        payment_link_token=token
    )

    if (
        order.payment_link_expires_at
        and
        timezone.now()
        >
        order.payment_link_expires_at
    ):

        return render(
            request,
            "payment_expired.html"
        )

    return render(
        request,
        "payment_page.html",
        {
            "order": order
        }
    )




from django.views.decorators.http import require_POST
from django.utils import timezone


@require_POST
def submit_payment(request, token):

    order = get_object_or_404(
        Order,
        payment_link_token=token
    )

    trx_id = request.POST.get(
        "trx_id",
        ""
    ).strip()

    if not trx_id:

        return render(
            request,
            "payment_page.html",
            {
                "order": order,
                "error": "Transaction ID is required."
            }
        )

    existing_order = (
        Order.objects.filter(
            submitted_txn_id=trx_id
        )
        .exclude(id=order.id)
        .exists()
    )

    if existing_order:

        return render(
            request,
            "payment_page.html",
            {
                "order": order,
                "error": "This Transaction ID has already been used."
            }
        )

    order.submitted_txn_id = trx_id
    order.save()

    cached_transaction = (
        VerifiedTransactionCache.objects.filter(
            merchant=order.merchant,
            txn_id=trx_id,
            amount_received=order.total_amount,
            is_used=False
        )
        .first()
    )

    if cached_transaction:

        order.order_status = (
            "paid_ready_to_ship"
        )

        order.paid_at = (
            timezone.now()
        )

        order.save()

        cached_transaction.is_used = True
        cached_transaction.save()

        try:

            send_whatsapp_message(
                order.customer_phone,
                (
                    f"Payment verified successfully.\n\n"
                    f"Order #{order.id} is now being prepared."
                )
            )

        except Exception as e:

            print(
                "Customer WhatsApp Error:",
                str(e)
            )

        try:

            send_whatsapp_message(
                order.merchant.whatsapp_number,
                (
                    f"Payment received.\n\n"
                    f"Order #{order.id} is ready to ship."
                )
            )

        except Exception as e:

            print(
                "Merchant WhatsApp Error:",
                str(e)
            )

        return render(
            request,
            "payment_verified.html",
            {
                "order": order
            }
        )

    return render(
        request,
        "payment_submitted.html",
        {
            "order": order
        }
    )




import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re
from decimal import Decimal


def parse_bkash_sms(message):

    txn_match = re.search(
        r"(?:TrxID|TxnID)\s*:?\s*([A-Za-z0-9]+)",
        message,
        re.IGNORECASE
    )

    amount_match = re.search(
        r"Tk\.?\s*([\d,]+(?:\.\d+)?)",
        message,
        re.IGNORECASE
    )

    phone_match = re.search(
        r"from\s+(01\d{9})",
        message,
        re.IGNORECASE
    )

    txn_id = (
        txn_match.group(1)
        if txn_match
        else None
    )

    amount = None

    if amount_match:

        amount = Decimal(
            amount_match.group(1)
            .replace(",", "")
        )

    sender_phone = (
        phone_match.group(1)
        if phone_match
        else None
    )

    return {
        "txn_id": txn_id,
        "amount": amount,
        "sender_phone": sender_phone
    }

@csrf_exempt
def sms_webhook(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required"
            },
            status=405
        )

    try:

        data = json.loads(
            request.body
        )

        api_key = data.get(
            "api_key"
        )

        sender = data.get(
            "sender",
            ""
        )

        message = data.get(
            "message",
            ""
        )

        if not api_key:

            return JsonResponse(
                {
                    "success": False,
                    "error": "API key missing"
                },
                status=400
            )

        try:

            merchant = Merchant.objects.get(
                sms_api_key=api_key
            )

        except Merchant.DoesNotExist:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid API key"
                },
                status=403
            )

        parsed = parse_bkash_sms(
            message
        )

        txn_id = parsed["txn_id"]

        amount = parsed["amount"]

        sender_phone = parsed[
            "sender_phone"
        ]

        if not txn_id:

            return JsonResponse(
                {
                    "success": False,
                    "error": "TrxID not found"
                },
                status=400
            )

        if amount is None:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Amount not found"
                },
                status=400
            )

        existing_transaction = (
            VerifiedTransactionCache.objects.filter(
                txn_id=txn_id
            )
            .first()
        )

        if existing_transaction:

            return JsonResponse(
                {
                    "success": True,
                    "message": "Transaction already processed"
                }
            )

        transaction = (
            VerifiedTransactionCache.objects.create(
                merchant=merchant,
                txn_id=txn_id,
                amount_received=amount,
                sender_phone=sender_phone,
                source=sender.lower()
            )
        )

        print("========== ORDER MATCHING ==========")
        print("Merchant:", merchant.id)
        print("TxnID:", txn_id)
        print("Amount:", amount)
        print("===================================")



        orders = Order.objects.filter(
            merchant=merchant
        )

        for o in orders:
            print(
                o.id,
                o.submitted_txn_id,
                o.total_amount,
                o.order_status
            )

        order = (
            Order.objects.filter(
                merchant=merchant,
                submitted_txn_id=txn_id,
                total_amount=amount,
                order_status="approved_awaiting_payment"
            )
            .order_by("-created_at")
            .first()
        )

        if order:

            order.order_status = (
                "paid_ready_to_ship"
            )

            order.paid_at = (
                timezone.now()
            )

            order.save()

            transaction.is_used = True
            transaction.save()

            try:

                send_whatsapp_message(
                    order.customer_phone,
                    (
                        f"Payment verified successfully.\n\n"
                        f"Order #{order.id} is now being prepared."
                    )
                )

            except Exception as e:

                print(
                    "Customer WhatsApp Error:",
                    str(e)
                )

            try:

                send_whatsapp_message(
                    merchant.whatsapp_number,
                    (
                        f"Payment received.\n\n"
                        f"Order #{order.id} is ready to ship."
                    )
                )

            except Exception as e:

                print(
                    "Merchant WhatsApp Error:",
                    str(e)
                )

            return JsonResponse(
                {
                    "success": True,
                    "matched_order": order.id
                }
            )

        return JsonResponse(
            {
                "success": True,
                "message": "Transaction cached for future matching."
            }
        )

    except Exception as e:

        print(
            "SMS WEBHOOK ERROR:",
            str(e)
        )

        return JsonResponse(
            {
                "success": False,
                "error": str(e)
            },
            status=500
        )