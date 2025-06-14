from rest_framework import status, generics, permissions
from posts.models import Comment, CommentLike, Like, Post, PostAttachment
from .serializers import (
    PostAttachmentSerializer,
    PostSerializer,
    CommentSerializer,
    PostLikeSerializer,
    PostCreateSerializer,
    SharePostSerializer,
)
from rest_framework.views import APIView
from core.responses import CustomResponse
from notifications.models import Notification
from core.pagination import CustomPagination


class PostView(APIView):
    pagination_class = CustomPagination
    
    def get(self, request):
        group_id = request.query_params.get("group_id")
        event_id = request.query_params.get("event_id")
        user_ids = [request.user.id]
        if request.user.is_authenticated:
            for user in request.user.friends.all():
                user_ids.append(user.id)
            if group_id:
                posts = Post.objects.filter(created_by_id__in=list(user_ids), group=group_id)
            elif event_id:
                posts = Post.objects.filter(created_by_id__in=list(user_ids), event=event_id)
            else:
                posts = Post.objects.filter(created_by_id__in=list(user_ids)).exclude(group__isnull=False).exclude(event__isnull=False)
        else:
            posts = []
        paginator = self.pagination_class()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostSerializer(paginated_posts, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            pagination=paginator.get_pagination_meta(),
            status=status.HTTP_200_OK,
            message="Posts retrieved successfully",
        )


class PostDetailView(APIView):
    def get(self, request, pk):
        try:
            if request.user.is_authenticated:
                post = Post.objects.get(pk=pk)
            else:
                post = Post.objects.get(pk=pk)
            serializer = PostSerializer(post, context={"request": request})
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message="Post retrieved successfully",
            )
        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Post not found"
            )

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return CustomResponse(
                data=None,
                status=status.HTTP_401_UNAUTHORIZED,
                message="Authentication required to delete a post",
            )
        try:
            post = Post.objects.get(pk=pk)
            post.delete()
            return CustomResponse(
                data={}, status=status.HTTP_200_OK, message="Post deleted successfully"
            )
        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Post not found"
            )


class PostCreateAPIView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(
            request, *args, **kwargs
        )  # Just create, no need to capture response
        queryset = self.get_queryset().order_by(
            "-created_at"
        )  # or whatever ordering you want
        serializer = PostSerializer(queryset, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
            message="Post created successfully",
        )


class PostUpdateAPIView(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = (
            self.get_object()
        )  # Because in update, self.get_object() gives you the updated instance
        serializer = PostSerializer(instance, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message="Post updated successfully",
        )


class PostLikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            reaction_type = request.data.get(
                "reaction_type", "like"
            )  # Default to 'like' if not specified

            # Validate reaction type
            if reaction_type not in dict(Like.REACTION_CHOICES):
                return CustomResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="Invalid reaction type",
                )

            # Check if a Like by this user already exists
            like = post.likes.filter(created_by=request.user).first()

            if not like:
                # Create a Like object with reaction
                like = Like.objects.create(
                    created_by=request.user, post=post, reaction_type=reaction_type
                )

                # Create notification for the post owner
                if post.created_by != request.user:
                    Notification.objects.create(
                        recipient=post.created_by,
                        sender=request.user,
                        notification_type="like",
                        post=post,
                    )

                message = f"Post {reaction_type} reaction added successfully"
            else:
                if like.reaction_type == reaction_type:
                    # If same reaction, remove it (unlike)
                    like.delete()
                    message = f"Post {reaction_type} reaction removed successfully"
                else:
                    # If different reaction, update it
                    like.reaction_type = reaction_type
                    like.save()
                    message = f"Post reaction updated to {reaction_type} successfully"

            serializer = PostSerializer(post, context={"request": request})
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message=message,
            )

        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Post not found",
            )


class AddCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return CustomResponse(
                data={},
                message="Post not found",
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            comment = serializer.save(post=post)

            # Create notification for the post owner
            if post.created_by != request.user:
                Notification.objects.create(
                    recipient=post.created_by,
                    sender=request.user,
                    notification_type="comment",
                    post=post,
                    comment=comment,
                )

            # If this is a reply, also notify the parent comment's author
            parent_comment_id = request.data.get("parent")
            if parent_comment_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_comment_id)
                    if parent_comment.created_by != request.user:
                        Notification.objects.create(
                            recipient=parent_comment.created_by,
                            sender=request.user,
                            notification_type="reply",
                            post=post,
                            comment=comment,
                        )
                except Comment.DoesNotExist:
                    pass

            return CustomResponse(
                data=serializer.data,
                message="Comment added successfully",
                status=status.HTTP_201_CREATED,
            )

        return CustomResponse(
            data={}, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class CommentLikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            reaction_type = request.data.get(
                "reaction_type", "like"
            )  # Default to 'like' if not specified

            # Validate reaction type
            if reaction_type not in dict(CommentLike.REACTION_CHOICES):
                return CustomResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="Invalid reaction type",
                )

            # Check if a Like by this user already exists
            like = comment.likes.filter(created_by=request.user).first()

            if not like:
                # Create a Like object with reaction
                like = CommentLike.objects.create(
                    created_by=request.user,
                    comment=comment,
                    reaction_type=reaction_type,
                )

                # Create notification for the comment owner
                if comment.created_by != request.user:
                    Notification.objects.create(
                        recipient=comment.created_by,
                        sender=request.user,
                        notification_type="comment_like",
                        post=comment.post,
                        comment=comment,
                    )

                message = f"Comment {reaction_type} reaction added successfully"
            else:
                if like.reaction_type == reaction_type:
                    # If same reaction, remove it (unlike)
                    like.delete()
                    message = f"Comment {reaction_type} reaction removed successfully"
                else:
                    # If different reaction, update it
                    like.reaction_type = reaction_type
                    like.save()
                    message = (
                        f"Comment reaction updated to {reaction_type} successfully"
                    )

            serializer = CommentSerializer(comment, context={"request": request})
            return CustomResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message=message,
            )

        except Comment.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND,
                message="Comment not found",
            )


class UpdateCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return CustomResponse(
                data={},
                message="Comment not found",
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(
                data=serializer.data,
                message="Comment updated successfully",
                status=status.HTTP_200_OK,
            )

        return CustomResponse(
            data={}, message=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class DeleteCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            comment.delete()
            return CustomResponse(
                data={},
                message="Comment deleted successfully",
                status=status.HTTP_200_OK,
            )
        except Comment.DoesNotExist:
            return CustomResponse(
                data={}, message="Comment not found", status=status.HTTP_404_NOT_FOUND
            )


class SharePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SharePostSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            post = serializer.save()
            posts = Post.objects.all()
            posts = PostSerializer(posts, many=True, context={"request": request})
            return CustomResponse(
                data=posts.data,
                message="Post shared successfully",
                status=status.HTTP_201_CREATED,
            )
        return CustomResponse(
            data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class SavePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            user = request.user

            if post in user.saved_posts.all():
                user.saved_posts.remove(post)
                message = "Post removed from saved posts"
            else:
                user.saved_posts.add(post)
                message = "Post saved successfully"

            serializer = PostSerializer(post, context={"request": request})
            return CustomResponse(
                data=serializer.data, status=status.HTTP_200_OK, message=message
            )
        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Post not found"
            )

class SavedPostsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        saved_posts = request.user.saved_posts.all()
        serializer = PostSerializer(
            saved_posts, many=True, context={"request": request}
        )
        return CustomResponse(data=serializer.data, status=status.HTTP_200_OK)


class AddToFavoritesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            user = request.user

            if post in user.favorites.all():
                user.favorites.remove(post)
                message = "Post removed from favorites"
            else:
                user.favorites.add(post)
                message = "Post added to favorites"

            serializer = PostSerializer(post, context={"request": request})
            return CustomResponse(
                data=serializer.data, status=status.HTTP_200_OK, message=message
            )
        except Post.DoesNotExist:
            return CustomResponse(
                status=status.HTTP_404_NOT_FOUND, message="Post not found"
            )

class FavoritesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        favorites = request.user.favorites.all()
        serializer = PostSerializer(favorites, many=True, context={"request": request})
        return CustomResponse(data=serializer.data, status=status.HTTP_200_OK)

class PhotoView(APIView):
    pagination_class = CustomPagination
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        photos = PostAttachment.objects.filter(created_by=request.user)
        paginator = self.pagination_class()
        paginated_photos = paginator.paginate_queryset(photos, request)
        serializer = PostAttachmentSerializer(paginated_photos, many=True, context={"request": request})
        return CustomResponse(
            data=serializer.data,
            pagination=paginator.get_pagination_meta(),
            status=status.HTTP_200_OK,
            message="Photos retrieved successfully",
        )
    
