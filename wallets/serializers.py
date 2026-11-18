from decimal import Decimal
from rest_framework import serializers
from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user_id', 'currency', 'balance', 'created_at']
        read_only_fields = ['id', 'balance', 'created_at']

class DepositSerializer(serializers.Serializer):
    wallet_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    reference_id = serializers.CharField(max_length=255)

class TransferSerializer(serializers.Serializer):
    source_wallet_id = serializers.UUIDField()
    destination_wallet_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    reference_id = serializers.CharField(max_length=255)