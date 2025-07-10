from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from auctions.models import Auction

# Create your tests here.
User = get_user_model()

class PaymentViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='plamen', password='testpass')
        self.auction = Auction.objects.create(
            photo=...,  # create or mock a photo
            start_time=...,
            end_time=...,
            starting_bid=10.00,
            current_highest_bid=50.00,
            highest_bidder=self.user,
            is_active=False
        )

    def test_payment_view_accessible_by_winner(self):
        self.client.login(username='plamen', password='testpass')
        response = self.client.get(reverse('auction-payment', kwargs={'pk': self.auction.pk}))
        self.assertEqual(response.status_code, 200)