from django.contrib import admin
from .models import Post, Comment, Like


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "created_at",
        "get_like_count",
        "comment_count",
    )
    list_filter = ("status", "created_at", "tags")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "content", "author__username")
    readonly_fields = ("created_at", "updated_at")

    def get_like_count(self, obj):
        return obj.get_like_count()

    get_like_count.short_description = "Likes"

    def comment_count(self, obj):
        return obj.comment_set.count()

    comment_count.short_description = "Comments"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "content_preview", "created_at")
    list_filter = ("created_at", "post")
    search_fields = ("content", "user__username", "post__title")

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content"


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("post__title", "user__username")
