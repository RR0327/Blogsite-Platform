import django
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from taggit.managers import TaggableManager
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinLengthValidator
from django.utils.html import strip_tags
import uuid

STATUS_CHOICES = (
    ("draft", "Draft"),
    ("published", "Published"),
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Post(TimeStampedModel):
    title = models.CharField(max_length=200, validators=[MinLengthValidator(5)])
    slug = models.SlugField(unique=True, blank=True, max_length=250)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(validators=[MinLengthValidator(50)])
    excerpt = models.TextField(
        max_length=300, blank=True, help_text="Brief description of the post"
    )
    featured_image = models.ImageField(
        upload_to="posts/%Y/%m/%d/", blank=True, null=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(
        default=0, help_text="Reading time in minutes"
    )
    tags = TaggableManager()
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["author", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-generate excerpt if empty
        if not self.excerpt and self.content:
            self.excerpt = strip_tags(self.content)[:297] + "..."

        # Calculate reading time (average reading speed: 200 words per minute)
        if self.content:
            word_count = len(strip_tags(self.content).split())
            self.reading_time = max(1, round(word_count / 200))

        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    def total_likes(self):
        return self.like_set.count()

    def get_like_count(self):
        return self.like_set.count()

    def user_has_liked(self, user):
        if user.is_authenticated:
            return self.like_set.filter(user=user).exists()
        return False

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=["view_count"])


class Comment(TimeStampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(validators=[MinLengthValidator(10)])
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

    def get_replies(self):
        return self.replies.filter(is_approved=True)


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return self.email
