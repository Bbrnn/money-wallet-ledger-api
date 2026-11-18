from decimal import Decimal
from django.db import transaction, DatabaseError
from .models import Wallet, LedgerTransaction

class LedgerService:
    
    @staticmethod
    @transaction.atomic
    def deposit(wallet_id: str, amount: Decimal, reference_id: str) -> Wallet:
        """
        Safely deposits funds into a single wallet within an atomic transaction.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")

        # Lock the target wallet row to prevent concurrent balance mutations
        try:
            wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        except Wallet.DoesNotExist:
            raise ValueError("Target wallet does not exist.")

        # Update balance
        wallet.balance += amount
        wallet.save()

        # Log immutable transaction
        LedgerTransaction.objects.create(
            reference_id=reference_id,
            amount=amount,
            source_wallet=None,
            destination_wallet=wallet,
            status="SUCCESS"
        )

        return wallet

    @staticmethod
    @transaction.atomic
    def transfer(source_wallet_id: str, destination_wallet_id: str, amount: Decimal, reference_id: str) -> dict:
        """
        Executes an atomic, race-condition-free fund transfer between two wallets.
        Locks wallets in a consistent sorted order to avoid database deadlocks.
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero.")
        
        if source_wallet_id == destination_wallet_id:
            raise ValueError("Source and destination wallets cannot be the same.")

        # 1. Sort IDs deterministically to prevent deadlocks when locking rows concurrently
        wallet_ids = sorted([str(source_wallet_id), str(destination_wallet_id)])

        # 2. Acquire row-level locks on both wallets simultaneously
        locked_wallets = Wallet.objects.select_for_update().filter(id__in=wallet_ids)
        wallet_map = {str(w.id): w for w in locked_wallets}

        source = wallet_map.get(str(source_wallet_id))
        destination = wallet_map.get(str(destination_wallet_id))

        if not source or not destination:
            raise ValueError("One or both wallets do not exist.")

        # 3. Verify sufficient balance (backed by database CHECK constraint as secondary defense)
        if source.balance < amount:
            raise ValueError("Insufficient funds in source wallet.")

        # 4. Perform debit and credit updates
        source.balance -= amount
        source.save()

        destination.balance += amount
        destination.save()

        # 5. Record the immutable ledger entry
        transaction_record = LedgerTransaction.objects.create(
            reference_id=reference_id,
            amount=amount,
            source_wallet=source,
            destination_wallet=destination,
            status="SUCCESS"
        )

        return {
            "status": "success",
            "reference_id": transaction_record.reference_id,
            "source_balance": str(source.balance),
            "destination_balance": str(destination.balance)
        }