from django.db import models
from merchants.models import Merchant

# home/models.py

class Order(models.Model):

    STATUS_CHOICES = (
        ('awaiting_stock_check', 'Awaiting Stock Check'),
        ('approved_awaiting_payment', 'Approved Awaiting Payment'),
        ('paid_ready_to_ship', 'Paid Ready To Ship'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    customer_name = models.CharField(max_length=100)

    customer_phone = models.CharField(max_length=20)

    delivery_address = models.TextField()

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    submitted_txn_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True
    )

    order_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='awaiting_stock_check'
    )

    payment_link_token = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    payment_link_expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    order_items = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"Order #{self.id}"
    

class OrderImage(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='order_images/'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order #{self.order.id} Image"


class VerifiedTransactionCache(models.Model):

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE
    )

    txn_id = models.CharField(
        max_length=50,
        unique=True
    )

    amount_received = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    sender_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    is_used = models.BooleanField(
        default=False
    )

    source = models.CharField(
        max_length=20,
        default="sms"
    )

    received_at = models.DateTimeField(
        auto_now_add=True
    )
    


class NotificationLog(models.Model):

    CHANNEL_CHOICES = (
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES
    )

    recipient = models.CharField(max_length=20)

    message = models.TextField()

    sent_successfully = models.BooleanField(default=False)

    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel} - Order {self.order.id}"