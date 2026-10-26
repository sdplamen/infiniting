from django.contrib.auth import get_user_model
from rest_framework import serializers

from articles.models import Article
from auctions.models import Auction, Bid
from groups.models import Group
from photos.models import Photo, Like, Comment, Rating


UserModel = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = UserModel.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class PhotoSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Photo
        fields = ['id', 'caption', 'image', 'uploaded_at', 'owner']
        read_only_fields = ['id', 'uploaded_at', 'owner']

class LikeSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)
    photo = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'owner', 'photo', 'created_at']
        read_only_fields = ['id', 'owner', 'photo', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)
    photo = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'text', 'owner', 'photo', 'created_at']
        read_only_fields = ['id', 'owner', 'photo', 'created_at']

class RatingSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)
    photo = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'score', 'owner', 'photo', 'created_at']
        read_only_fields = ['id', 'owner', 'photo', 'created_at']

class ArticleSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'created_at', 'updated_at', 'owner']
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

class BidSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)
    auction = serializers.PrimaryKeyRelatedField(queryset=Auction.objects.all())

    class Meta:
        model = Bid
        fields = ['id', 'amount', 'owner', 'auction', 'bid_time']
        read_only_fields = ['id', 'owner', 'bid_time']

class AuctionSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)
    bids = BidSerializer(many=True, read_only=True)

    class Meta:
        model = Auction
        fields = ['id', 'start_time', 'end_time',
                  'starting_bid', 'current_highest_bid', 'highest_bidder', 'is_active', 'owner', 'bids']
        read_only_fields = ['id', 'current_highest_bid', 'highest_bidder', 'is_active', 'owner', 'bids']

class GroupSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)
    members = SimpleUserSerializer(many=True, read_only=True)

    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'creator', 'members', 'member_ids', 'created_at']
        read_only_fields = ['id', 'creator', 'created_at']

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])

        group = Group.objects.create(**validated_data)

        if member_ids:
            group.members.set(member_ids)

        if self.context['request'].user.is_authenticated:
            group.members.add(self.context['request'].user)

        return group

    def update(self, instance, validated_data):
        member_ids = validated_data.pop('member_ids', None)

        instance = super().update(instance, validated_data)

        if member_ids is not None:
            instance.members.set(member_ids)

        return instance
