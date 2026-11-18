import uuid
from django.db import models
from django.db.models import Q, CheckConstraint

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    currency = models.CharField(max_length=3, default="KES")
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"
        constraints = [
            # Database-level guarantee: balance can NEVER be negative
            CheckConstraint(
                check=Q(balance__gte=0),
                name="positive_balance_check"
            )
        ]

    def __str__(self):
        return f"Wallet {self.id} ({self.currency} {self.balance})"


class LedgerTransaction(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_id = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    source_wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.PROTECT, 
        related_name="outgoing_transactions",
        null=True, 
        blank=True
    )
    destination_wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.PROTECT, 
        related_name="incoming_transactions",
        null=True, 
        blank=True
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_transactions"

    def __str__(self):
        return f"Tx {self.reference_id} - {self.amount} ({self.status})"


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    wallet_id = models.UUIDField()
    request_hash = models.CharField(max_length=64)
    response_status = models.IntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "idempotency_keys"

    def __str__(self):
        return f"Idempotency Key: {self.key}"