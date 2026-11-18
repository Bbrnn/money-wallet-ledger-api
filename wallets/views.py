from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import WalletSerializer, DepositSerializer, TransferSerializer
from .services import LedgerService
from .models import Wallet

# Create your views here.
class WalletCreateListView(APIView):
    def get(self, request):
        wallets = Wallet.objects.all()
        serializer = WalletSerializer(wallets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WalletSerializer(data=request.data)
        if serializer.is_valid():
            wallet = serializer.save()
            return Response(WalletSerializer(wallet).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DepositAPIView(APIView):
    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                wallet = LedgerService.deposit(
                    wallet_id=str(data['wallet_id']),
                    amount=data['amount'],
                    reference_id=data['reference_id']
                )
                return Response({
                    "status": "success",
                    "wallet_id": str(wallet.id),
                    "new_balance": str(wallet.balance)
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransferAPIView(APIView):
    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                result = LedgerService.transfer(
                    source_wallet_id=str(data['source_wallet_id']),
                    destination_wallet_id=str(data['destination_wallet_id']),
                    amount=data['amount'],
                    reference_id=str(data['reference_id'])
                )
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
