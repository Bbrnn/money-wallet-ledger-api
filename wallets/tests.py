from decimal import Decimal
import concurrent.futures
from django.test import TransactionTestCase, TestCase
from django.urls import reverse
from django.db import connection
from rest_framework import status
from rest_framework.test import APIClient
from wallets.models import Wallet, IdempotencyKey
from wallets.services import LedgerService

class LedgerUnitTestCase(TestCase):
    def setUp(self):
        self.wallet = Wallet.objects.create(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            balance=Decimal("1000.00"),
            currency="KES"
        )

    def test_deposit_success(self):
        """Test safe deposit increases wallet balance correctly."""
        updated = LedgerService.deposit(
            wallet_id=str(self.wallet.id),
            amount=Decimal("500.00"),
            reference_id="dep_001"
        )
        self.assertEqual(updated.balance, Decimal("1500.00"))

    def test_deposit_invalid_amount(self):
        """Test that negative or zero deposits raise a ValueError."""
        with self.assertRaises(ValueError):
            LedgerService.deposit(
                wallet_id=str(self.wallet.id),
                amount=Decimal("-50.00"),
                reference_id="dep_err"
            )


class LedgerIdempotencyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.wallet_a = Wallet.objects.create(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            balance=Decimal("2000.00"),
            currency="KES"
        )
        self.wallet_b = Wallet.objects.create(
            user_id="987f6543-e21b-43d2-b654-426614174999",
            balance=Decimal("0.00"),
            currency="KES"
        )

    def test_idempotent_transfer_request(self):
        """Test that repeating a request with the same Idempotency-Key returns cached results safely."""
        url = reverse('wallet-transfer')
        payload = {
            "source_wallet_id": str(self.wallet_a.id),
            "destination_wallet_id": str(self.wallet_b.id),
            "amount": "500.00",
            "reference_id": "ref_idem_01"
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "test-key-xyz-123"}

        # First request (should execute)
        response_1 = self.client.post(url, payload, format='json', **headers)
        self.assertEqual(response_1.status_code, status.HTTP_200_OK)

        # Modify balance manually to see if second request bypasses service and uses cache
        self.wallet_a.balance = Decimal("2000.00")
        self.wallet_a.save()

        # Second request with same key (should return cached response without re-executing transfer)
        response_2 = self.client.post(url, payload, format='json', **headers)
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_1.json(), response_2.json())


class LedgerConcurrencyTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.wallet_a = Wallet.objects.create(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            balance=Decimal("1000.00"),
            currency="KES"
        )
        self.wallet_b = Wallet.objects.create(
            user_id="987f6543-e21b-43d2-b654-426614174999",
            balance=Decimal("0.00"),
            currency="KES"
        )

    def test_concurrent_transfers_prevent_race_conditions(self):
        """
        Simulates 10 threads trying to simultaneously transfer 150 KES each 
        from Wallet A (total balance 1000 KES). Ensures balance never dips below zero 
        and pessimistic locking handles race conditions safely under heavy load.
        """
        num_threads = 10
        transfer_amount = Decimal("150.00")

        def execute_transfer(i):
            try:
                return LedgerService.transfer(
                    source_wallet_id=str(self.wallet_a.id),
                    destination_wallet_id=str(self.wallet_b.id),
                    amount=transfer_amount,
                    reference_id=f"concurrent_ref_{i}"
                )
            except Exception as e:
                return {"status": "failed", "error": str(e)}
            finally:
                # Ensure thread-local database session is closed so DB teardown succeeds
                connection.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(execute_transfer, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.wallet_a.refresh_from_db()
        self.wallet_b.refresh_from_db()

        successes = [r for r in results if r.get("status") == "success"]
        failures = [r for r in results if r.get("status") == "failed"]

        # Assertions
        self.assertGreaterEqual(self.wallet_a.balance, Decimal("0.00"))
        self.assertEqual(len(successes), 6)  # 6 * 150 = 900 (leaves 100 in A)
        self.assertEqual(len(failures), 4)   # Remaining 4 fail due to insufficient funds
        self.assertEqual(self.wallet_a.balance, Decimal("100.00"))
        self.assertEqual(self.wallet_b.balance, Decimal("900.00"))