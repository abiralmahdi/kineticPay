from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid



class SubscriptionPlan(models.Model):
    PLAN_CHOICES = (
        ('starter', 'Starter'),
        ('business', 'Business'),
        ('premium', 'Premium'),
    )

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=30, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)

    max_orders_per_month = models.IntegerField(default=100, blank=True, null=True)

    unlimited = models.BooleanField(default=False)

    sms_sync_enabled = models.BooleanField(default=False)
    api_sync_enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Merchant(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='merchant_profile'
    )

    business_name = models.CharField(max_length=100)

    slug = models.SlugField(
        max_length=50,
        unique=True
    )

    whatsapp_number = models.CharField(max_length=20)

    mfs_payment_number = models.CharField(max_length=20)

    is_active_merchant = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    sms_api_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True
    )

    def __str__(self):
        return self.business_name


class MerchantSubscription(models.Model):

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    start_date = models.DateTimeField(default=timezone.now)

    end_date = models.DateTimeField()

    auto_renew = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.merchant.business_name} - {self.plan.name}"