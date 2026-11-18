from django.urls import path
from .views import WalletCreateListView, DepositAPIView, TransferAPIView

urlpatterns = [
    path('wallets/', WalletCreateListView.as_view(), name='wallet-list-create'),
    path('deposits/', DepositAPIView.as_view(), name='wallet-deposit'),
    path('transfers/', TransferAPIView.as_view(), name='wallet-transfer'),
]