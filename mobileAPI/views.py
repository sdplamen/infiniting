from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from photos.models import Photo, Like, Comment, Rating
from mobileAPI.serializers import PhotoSerializer, LikeSerializer, CommentSerializer, RatingSerializer
from mobileAPI.permissions import IsAdminOrReadOnly, IsAuthenticatedAndOwner

UserModel = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = UserModel.objects.all()
    serializer_class = PhotoSerializer
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