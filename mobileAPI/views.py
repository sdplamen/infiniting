from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from articles.models import Article
from auctions.models import Auction, Bid
from groups.models import Group
from photos.models import Photo, Like, Comment, Rating
from mobileAPI.permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly
from mobileAPI.serializers import PhotoSerializer, LikeSerializer, CommentSerializer, RatingSerializer, \
    UserRegistrationSerializer, ArticleSerializer, AuctionSerializer, BidSerializer, GroupSerializer

UserModel = get_user_model()


def _photographer_or_400(user):
    photographer = getattr(user, 'photographer', None)
    if photographer is None:
        raise ValidationError('You need a photographer profile for this.')
    return photographer


def _filter_by_photo(queryset, request):
    """Optional ?photo=<id> filter for photo-related lists."""
    photo_id = request.query_params.get('photo')
    if photo_id is None:
        return queryset
    if not photo_id.isdigit():
        raise ValidationError({'photo': 'Must be a photo id.'})
    return queryset.filter(photo_id=photo_id)


class RegisterView(generics.CreateAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


# --- photos -----------------------------------------------------------------

class PhotoMixin:
    serializer_class = PhotoSerializer
    permission_classes = [IsOwnerOrReadOnly]
    owner_paths = ['author.user']

    def get_queryset(self):
        return Photo.objects.for_cards().with_counts().order_by('-uploaded_at', '-pk')


class PhotoListCreateAPIView(PhotoMixin, generics.ListCreateAPIView):
    def perform_create(self, serializer):
        serializer.save(author=_photographer_or_400(self.request.user))

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # re-read so the response carries the annotated counts
        photo = self.get_queryset().get(pk=response.data['id'])
        response.data = self.get_serializer(photo).data
        return response


class PhotoDetailAPIView(PhotoMixin, generics.RetrieveUpdateDestroyAPIView):
    pass


# --- likes, comments, ratings -------------------------------------------------

class LikeListCreateAPIView(generics.ListCreateAPIView):
    """With ?photo=<id>: that photo's likes. Without: the current user's likes."""
    serializer_class = LikeSerializer
    permission_classes = [IsOwnerOrReadOnly]
    owner_paths = ['user']

    def get_queryset(self):
        queryset = Like.objects.select_related('user').order_by('-created_at')
        if 'photo' in self.request.query_params:
            return _filter_by_photo(queryset, self.request)
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LikeDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = Like.objects.select_related('user')
    serializer_class = LikeSerializer
    permission_classes = [IsOwnerOrReadOnly]
    owner_paths = ['user']


class CommentListCreateAPIView(generics.ListCreateAPIView):
    """Comments are public on the website too; filter with ?photo=<id>."""
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
    owner_paths = ['user']

    def get_queryset(self):
        return _filter_by_photo(Comment.objects.select_related('user').order_by('-created_at'), self.request)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related('user', 'photo__author__user')
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
    # as on the website, the photo's author may also remove comments on it
    owner_paths = ['user', 'photo.author.user']

    def update(self, request, *args, **kwargs):
        # only the writer may edit the text; the photo's author may only delete
        if self.get_object().user != request.user:
            return Response({'detail': 'You can only edit your own comments.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class RatingListCreateAPIView(generics.ListCreateAPIView):
    """The current user's ratings (photos show their average in /photos/)."""
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filter_by_photo(
            Rating.objects.select_related('user__user').filter(user__user=self.request.user).order_by('-created_at'),
            self.request)

    def perform_create(self, serializer):
        serializer.save(user=_photographer_or_400(self.request.user))


class RatingDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    owner_paths = ['user.user']

    def get_queryset(self):
        return Rating.objects.select_related('user__user').filter(user__user=self.request.user)


# --- articles -----------------------------------------------------------------

class ArticleMixin:
    serializer_class = ArticleSerializer
    permission_classes = [IsOwnerOrReadOnly]
    owner_paths = ['author.user']

    def get_queryset(self):
        # same rule as the website: unapproved articles only for approvers and their author
        queryset = Article.objects.select_related('author__user').order_by('-created_at')
        user = self.request.user
        if user.has_perm('articles.can_approve_articles'):
            return queryset
        visible = Q(is_approved=True)
        if user.is_authenticated:
            visible |= Q(author__user=user)
        return queryset.filter(visible)


class ArticleListCreateAPIView(ArticleMixin, generics.ListCreateAPIView):
    def perform_create(self, serializer):
        serializer.save(author=_photographer_or_400(self.request.user))


class ArticleDetailAPIView(ArticleMixin, generics.RetrieveUpdateDestroyAPIView):
    pass


# --- auctions and bids ----------------------------------------------------------

class AuctionListCreateAPIView(generics.ListCreateAPIView):
    queryset = Auction.objects.select_related('highest_bidder').prefetch_related('bids__bidder').order_by('-start_time')
    serializer_class = AuctionSerializer
    permission_classes = [IsStaffOrReadOnly]  # auctions are run by staff, as on the website


class AuctionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Auction.objects.select_related('highest_bidder').prefetch_related('bids__bidder')
    serializer_class = AuctionSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_destroy(self, instance):
        # as on the website: ended auctions are kept, the winner still has to pay
        if instance.end_time <= timezone.now():
            raise ValidationError({'detail': 'An auction can only be deleted before it ends.'})
        instance.delete()


class BidListCreateAPIView(generics.ListCreateAPIView):
    """The current user's bids; POST places a bid."""
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bid.objects.select_related('bidder').filter(bidder=self.request.user)

    def perform_create(self, serializer):
        amount = serializer.validated_data['amount']
        with transaction.atomic():
            # lock the auction row so two bids at the same moment can't both "win"
            auction = (Auction.objects.select_for_update()
                       .select_related('photo__author')
                       .get(pk=serializer.validated_data['auction'].pk))
            now = timezone.now()
            if not auction.is_active or auction.end_time <= now:
                raise ValidationError({'auction': 'This auction is closed.'})
            if auction.start_time > now:
                raise ValidationError({'auction': 'This auction has not started yet.'})
            if auction.photo.author.user_id == self.request.user.id:
                raise ValidationError({'auction': "You can't bid on your own photo."})
            if amount <= auction.current_highest_bid:
                raise ValidationError({'amount': 'Your bid must be higher than the current highest bid.'})
            if amount <= auction.starting_bid:
                raise ValidationError({'amount': 'Your bid must be higher than the starting bid.'})

            serializer.save(bidder=self.request.user, auction=auction)
            auction.current_highest_bid = amount
            auction.highest_bidder = self.request.user
            auction.save(update_fields=['current_highest_bid', 'highest_bidder', 'updated_at'])


class BidDetailAPIView(generics.RetrieveAPIView):
    """Bids are final: they can be read but not changed or withdrawn."""
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bid.objects.select_related('bidder').filter(bidder=self.request.user)


# --- groups -----------------------------------------------------------------------

class GroupMixin:
    serializer_class = GroupSerializer
    permission_classes = [IsOwnerOrReadOnly]
    owner_paths = ['author']
    staff_can_edit = True  # the website lets staff edit and delete any group

    def get_queryset(self):
        return Group.visible_to(self.request.user).select_related('author').prefetch_related('members').order_by('name')


class GroupListCreateAPIView(GroupMixin, generics.ListCreateAPIView):
    def perform_create(self, serializer):
        group = serializer.save(author=self.request.user)
        group.members.add(self.request.user)


class GroupDetailAPIView(GroupMixin, generics.RetrieveUpdateDestroyAPIView):
    pass


class GroupMembershipAPIView(generics.GenericAPIView):
    """POST joins the group, DELETE leaves it."""
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        group = get_object_or_404(Group.visible_to(request.user), pk=pk)
        group.members.add(request.user)
        return Response(self.get_serializer(group).data)

    def delete(self, request, pk):
        group = get_object_or_404(Group.objects.all(), pk=pk)
        group.members.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
