from django.contrib.auth import get_user_model
from rest_framework import serializers
from photos.models import Photo, Like, Comment, Rating


UserModel = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email']

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