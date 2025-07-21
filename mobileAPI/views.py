from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from articles.models import Article
from auctions.models import Auction, Bid
from groups.models import Group
from photos.models import Photo, Like, Comment, Rating
from mobileAPI.serializers import PhotoSerializer, LikeSerializer, CommentSerializer, RatingSerializer, \
    UserRegistrationSerializer, ArticleSerializer, AuctionSerializer, BidSerializer, GroupSerializer
from mobileAPI.permissions import IsAdminOrReadOnly, IsAuthenticatedAndOwner, IsGroupCreatorOrAdmin

UserModel = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class PhotoListCreateAPIView(generics.ListCreateAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PhotoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'pk'

class LikeListCreateAPIView(generics.ListCreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticatedAndOwner]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Like.objects.filter(owner=self.request.user)
        return Like.objects.none()


class LikeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticatedAndOwner]
    lookup_field = 'pk'


class CommentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedAndOwner]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedAndOwner]
    lookup_field = 'pk'

class RatingListCreateAPIView(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticatedAndOwner]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RatingDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticatedAndOwner]
    lookup_field = 'pk'


class ArticleListCreateAPIView(generics.ListCreateAPIView) :
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer) :
        serializer.save(owner=self.request.user)


class ArticleDetailAPIView(generics.RetrieveUpdateDestroyAPIView) :
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'pk'


class AuctionListCreateAPIView(generics.ListCreateAPIView) :
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer) :
        serializer.save(owner=self.request.user)


class AuctionDetailAPIView(generics.RetrieveUpdateDestroyAPIView) :
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'pk'


class BidListCreateAPIView(generics.ListCreateAPIView) :
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticatedAndOwner]

    def perform_create(self, serializer) :
        auction = serializer.validated_data['auction']
        amount = serializer.validated_data['amount']

        if not auction.is_active :
            raise serializers.ValidationError("This auction is not active.")

        if auction.current_highest_bid and amount <= auction.current_highest_bid :
            raise serializers.ValidationError("Your bid must be higher than the current highest bid.")

        serializer.save(owner=self.request.user)

        auction.current_highest_bid = amount
        auction.highest_bidder = self.request.user
        auction.save()

    def get_queryset(self) :
        if self.request.user.is_authenticated :
            return Bid.objects.filter(owner=self.request.user)
        return Bid.objects.none()

class BidDetailAPIView(generics.RetrieveUpdateDestroyAPIView) :
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticatedAndOwner]
    lookup_field = 'pk'

class GroupListCreateAPIView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        group = serializer.save(creator=self.request.user)
        group.members.add(self.request.user)


class GroupDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    permission_classes = [IsGroupCreatorOrAdmin]
    lookup_field = 'pk'