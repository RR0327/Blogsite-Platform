from django import template
from blog.models import Post

register = template.Library()


@register.simple_tag
def recent_posts(count=5):
    return Post.objects.filter(status="Published").order_by("-created_at")[:count]
