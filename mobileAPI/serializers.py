from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from articles.models import Article
from auctions.models import Auction, Bid
from groups.models import Group
from photos.models import Photo, Like, Comment, Rating


UserModel = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email', 'password']

    def validate(self, attrs):
        # run Django's AUTH_PASSWORD_VALIDATORS, same as the web sign-up
        validate_password(attrs['password'], user=UserModel(username=attrs['username'], email=attrs.get('email', '')))
        return attrs

    def create(self, validated_data):
        # a Photographer profile is created by the post_save signal in users/signals.py
        return UserModel.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )


class PhotoSerializer(serializers.ModelSerializer):
    author = SimpleUserSerializer(source='author.user', read_only=True)
    image = serializers.ImageField(write_only=True, required=False)
    image_url = serializers.SerializerMethodField()
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.none(), required=False, allow_null=True)
    likes_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Photo
        fields = ['id', 'caption', 'image', 'image_url', 'group', 'uploaded_at', 'author',
                  'exif', 'likes_count', 'average_rating']
        read_only_fields = ['id', 'uploaded_at', 'author', 'exif']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request is not None:
            # same choice as the web upload form: groups the user can see
            fields['group'].queryset = Group.visible_to(request.user)
        return fields

    def get_image_url(self, photo) -> str | None:
        return photo.image.url if photo.image else None

    def validate(self, attrs):
        if self.instance is None and not attrs.get('image'):
            raise serializers.ValidationError({'image': 'An image file is required.'})
        return attrs


class LikeSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'photo', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate_photo(self, photo):
        if Like.objects.filter(user=self.context['request'].user, photo=photo).exists():
            raise serializers.ValidationError('You already like this photo.')
        return photo


class CommentSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'text', 'user', 'photo', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def update(self, instance, validated_data):
        validated_data.pop('photo', None)  # a comment can't be moved to another photo
        return super().update(instance, validated_data)


class RatingSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(source='user.user', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'score', 'user', 'photo', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate_photo(self, photo):
        if self.instance is None:
            photographer = getattr(self.context['request'].user, 'photographer', None)
            if Rating.objects.filter(user=photographer, photo=photo).exists():
                raise serializers.ValidationError('You already rated this photo; update that rating instead.')
        return photo

    def update(self, instance, validated_data):
        validated_data.pop('photo', None)  # a rating can't be moved to another photo
        return super().update(instance, validated_data)


class ArticleSerializer(serializers.ModelSerializer):
    author = SimpleUserSerializer(source='author.user', read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'is_approved', 'created_at', 'updated_at', 'author']
        read_only_fields = ['id', 'is_approved', 'created_at', 'updated_at', 'author']


class BidSerializer(serializers.ModelSerializer):
    bidder = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Bid
        fields = ['id', 'amount', 'bidder', 'auction', 'bid_time']
        read_only_fields = ['id', 'bidder', 'bid_time']

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError('A bid must be greater than zero.')
        return amount


class AuctionSerializer(serializers.ModelSerializer):
    highest_bidder = SimpleUserSerializer(read_only=True)
    bids = BidSerializer(many=True, read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Auction
        fields = ['id', 'photo', 'start_time', 'end_time', 'starting_bid', 'current_highest_bid',
                  'highest_bidder', 'is_active', 'is_open', 'bids', 'created_at']
        read_only_fields = ['id', 'current_highest_bid', 'highest_bidder', 'bids', 'created_at']

    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and end <= start:
            raise serializers.ValidationError({'end_time': 'The auction must end after it starts.'})
        if self.instance is not None and 'photo' in attrs and attrs['photo'] != self.instance.photo:
            raise serializers.ValidationError({'photo': "An auction's photo can't be changed."})
        return attrs


class GroupSerializer(serializers.ModelSerializer):
    author = SimpleUserSerializer(read_only=True)
    members = SimpleUserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'author', 'members', 'is_approved', 'created_at']
        read_only_fields = ['id', 'author', 'members', 'is_approved', 'created_at']
