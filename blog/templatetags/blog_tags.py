from django import template
from django.db.models import Count
from blog.models import Post
from taggit.models import Tag  # ✅ FIXED: Import Tag from taggit, not blog.models
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.inclusion_tag("blog/recent_posts.html")
def show_recent_posts(count=5):
    """
    Display recent published posts
    """
    recent_posts = (
        Post.objects.filter(status="published")
        .select_related("author")
        .order_by("-created_at")[:count]
    )
    return {"recent_posts": recent_posts}


@register.simple_tag
def get_popular_tags(count=15):
    """
    Get popular tags with post count
    """
    return (
        Tag.objects.annotate(num_posts=Count("taggit_taggeditem_items"))
        .filter(num_posts__gt=0)
        .order_by("-num_posts")[:count]
    )


@register.simple_tag
def get_total_posts():
    """
    Get total published posts count
    """
    return Post.objects.filter(status="published").count()


@register.simple_tag
def get_most_commented_posts(count=3):
    """
    Get most commented posts
    """
    return (
        Post.objects.filter(status="published")
        .annotate(total_comments=Count("comments"))
        .order_by("-total_comments")[:count]
    )


@register.simple_tag
def get_trending_posts(count=3):
    """
    Get trending posts (most viewed in last 7 days)
    """
    last_week = timezone.now() - timedelta(days=7)
    return Post.objects.filter(status="published", created_at__gte=last_week).order_by(
        "-view_count"
    )[:count]


@register.simple_tag
def get_featured_posts(count=3):
    """
    Get featured posts
    """
    return Post.objects.filter(status="published", is_featured=True).order_by(
        "-created_at"
    )[:count]


@register.filter
def truncate_words_custom(value, arg):
    """
    Custom filter to truncate words with custom length
    """
    try:
        words = value.split()
        if len(words) > arg:
            return " ".join(words[:arg]) + "..."
        return value
    except:
        return value


@register.filter
def reading_time_minutes(content):
    """
    Calculate reading time in minutes
    """
    try:
        word_count = len(content.split())
        return max(1, round(word_count / 200))
    except:
        return 1


@register.simple_tag(takes_context=True)
def user_has_liked(context, post):
    """
    Check if current user has liked a post
    """
    request = context["request"]
    if request.user.is_authenticated:
        return post.like_set.filter(user=request.user).exists()
    return False


@register.simple_tag
def get_authors_with_posts():
    """
    Get authors who have published posts
    """
    return (
        Post.objects.filter(status="published")
        .values_list("author__username", flat=True)
        .distinct()
    )


@register.simple_tag
def get_post_statistics():
    """
    Get blog statistics
    """
    return {
        "total_posts": Post.objects.filter(status="published").count(),
        "total_authors": Post.objects.filter(status="published")
        .values("author")
        .distinct()
        .count(),
        "total_comments": (
            Comment.objects.filter(is_approved=True).count()
            if "Comment" in globals()
            else 0
        ),
        "total_likes": Like.objects.count() if "Like" in globals() else 0,
    }
