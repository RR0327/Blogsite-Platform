from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Post, Comment, Like, UserProfile, NewsletterSubscription
from .forms import (
    CommentForm,
    PostForm,
    CustomUserCreationForm,
    UserProfileForm,
    NewsletterSubscriptionForm,
)
from taggit.models import Tag


# Authentication Views
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get("username")
            messages.success(
                request, f"🎉 Account created for {username}! You can now log in."
            )
            return redirect("login")
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


def custom_logout(request):
    """Custom logout view that shows confirmation message"""
    logout(request)
    messages.success(request, "👋 You have been successfully logged out!")
    return redirect("blog:post_list")


# Core Blog Views
class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 6

    def get_queryset(self):
        queryset = (
            Post.objects.filter(status="published")
            .select_related("author")
            .prefetch_related("tags")
        )

        # Search functionality
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(excerpt__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            ).distinct()

        # Filter by tag
        tag_slug = self.request.GET.get("tag")
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Filter by author
        author = self.request.GET.get("author")
        if author:
            queryset = queryset.filter(author__username=author)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["featured_posts"] = Post.objects.filter(
            status="published", is_featured=True
        )[:3]

        # Get popular tags
        context["popular_tags"] = (
            Tag.objects.annotate(num_posts=Count("taggit_taggeditem_items"))
            .filter(num_posts__gt=0)
            .order_by("-num_posts")[:10]
        )

        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"

    def get_queryset(self):
        # Allow authors to view their own drafts, but only show published posts to others
        queryset = Post.objects.all()

        # If user is authenticated and is the author, they can see their drafts
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(status="published") | Q(author=self.request.user, status="draft")
            )
        else:
            # Non-authenticated users can only see published posts
            queryset = queryset.filter(status="published")

        return queryset.select_related("author").prefetch_related("tags", "comments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # Only increment view count for published posts
        if post.status == "published":
            post.increment_view_count()

        # Get related posts (only published ones)
        related_posts = (
            Post.objects.filter(status="published", tags__in=post.tags.all())
            .exclude(id=post.id)
            .distinct()[:3]
        )

        context["form"] = CommentForm()

        # Only show approved comments
        context["comments"] = post.comments.filter(
            parent__isnull=True, is_approved=True
        ).order_by("-created_at")
        context["related_posts"] = related_posts

        # Like functionality
        if self.request.user.is_authenticated:
            context["user_has_liked"] = post.user_has_liked(self.request.user)
        else:
            context["user_has_liked"] = False

        # Add post status to context for template
        context["is_draft"] = post.status == "draft"
        context["is_published"] = post.status == "published"

        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "✅ Post created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.object.slug})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        messages.success(self.request, "✅ Post updated successfully!")
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.object.slug})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "blog/post_confirm_delete.html"
    success_url = "/dashboard/"

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def delete(self, request, *args, **kwargs):
        messages.success(request, "✅ Post deleted successfully!")
        return super().delete(request, *args, **kwargs)


# Dashboard and User Management
class DashboardView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/dashboard.html"
    context_object_name = "posts"
    paginate_by = 8

    def get_queryset(self):
        return (
            Post.objects.filter(author=self.request.user)
            .select_related("author")
            .prefetch_related("tags")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_posts = Post.objects.filter(author=self.request.user)

        # Statistics
        context["published_count"] = user_posts.filter(status="published").count()
        context["draft_count"] = user_posts.filter(status="draft").count()
        context["total_likes"] = sum(post.get_like_count() for post in user_posts)
        context["total_views"] = sum(post.view_count for post in user_posts)
        context["total_comments"] = sum(post.comments.count() for post in user_posts)

        # Recent activity
        context["recent_comments"] = Comment.objects.filter(
            post__author=self.request.user
        ).order_by("-created_at")[:5]

        # Popular posts
        context["popular_user_posts"] = user_posts.order_by("-view_count")[:3]

        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "blog/profile.html"

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, "✅ Profile updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_posts_count"] = Post.objects.filter(
            author=self.request.user
        ).count()
        context["user_published_posts"] = Post.objects.filter(
            author=self.request.user, status="published"
        ).count()
        return context


# Interaction Views
@login_required
def add_comment(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user

            # Handle reply comments
            parent_id = request.POST.get("parent_id")
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent = parent_comment

            comment.save()
            messages.success(request, "💬 Comment added successfully!")
        else:
            messages.error(request, "❌ Error adding comment. Please try again.")

    return redirect("blog:post_detail", slug=post.slug)


@login_required
def like_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        messages.info(request, "❤️ Post unliked!")
    else:
        messages.success(request, "❤️ Post liked!")

    return redirect("blog:post_detail", slug=post.slug)


@require_POST
@login_required
def ajax_like_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        liked = False
        message = "Post unliked"
    else:
        liked = True
        message = "Post liked"

    return JsonResponse(
        {"liked": liked, "like_count": post.get_like_count(), "message": message}
    )


# Discovery and Search Views
def posts_by_tag(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    posts_list = Post.objects.filter(status="published", tags__in=[tag])

    paginator = Paginator(posts_list, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "blog/posts_by_tag.html",
        {"tag": tag, "posts": page_obj, "total_posts": posts_list.count()},
    )


def advanced_search(request):
    query = request.GET.get("q", "")
    tag = request.GET.get("tag", "")
    author = request.GET.get("author", "")
    sort = request.GET.get("sort", "newest")

    posts = Post.objects.filter(status="published")

    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()

    if tag:
        posts = posts.filter(tags__slug=tag)

    if author:
        posts = posts.filter(author__username=author)

    # Sorting
    if sort == "popular":
        posts = posts.annotate(like_count=Count("like")).order_by(
            "-like_count", "-created_at"
        )
    elif sort == "views":
        posts = posts.order_by("-view_count", "-created_at")
    elif sort == "comments":
        posts = posts.annotate(comment_count=Count("comments")).order_by(
            "-comment_count", "-created_at"
        )
    else:  # newest
        posts = posts.order_by("-created_at")

    paginator = Paginator(posts, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get available filters
    available_tags = (
        Tag.objects.filter(taggit_taggeditem_items__content_object__in=posts)
        .distinct()
        .annotate(num_posts=Count("taggit_taggeditem_items"))
    )

    available_authors = (
        User.objects.filter(posts__in=posts)
        .distinct()
        .annotate(num_posts=Count("posts"))
    )

    context = {
        "posts": page_obj,
        "query": query,
        "tag": tag,
        "author": author,
        "sort": sort,
        "total_results": posts.count(),
        "available_tags": available_tags,
        "available_authors": available_authors,
    }

    return render(request, "blog/advanced_search.html", context)


def user_posts(request, username):
    user = get_object_or_404(User, username=username)
    posts_list = Post.objects.filter(author=user, status="published").order_by(
        "-created_at"
    )

    paginator = Paginator(posts_list, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # User statistics
    user_stats = {
        "total_posts": posts_list.count(),
        "total_likes": sum(post.get_like_count() for post in posts_list),
        "total_views": sum(post.view_count for post in posts_list),
        "join_date": user.date_joined,
    }

    context = {
        "profile_user": user,
        "posts": page_obj,
        "user_stats": user_stats,
    }

    return render(request, "blog/user_posts.html", context)


def trending_posts(request):
    # Posts from last 30 days, ordered by views
    last_month = timezone.now() - timedelta(days=30)
    posts_list = Post.objects.filter(
        status="published", created_at__gte=last_month
    ).order_by("-view_count", "-created_at")

    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "posts": page_obj,
        "time_period": "last 30 days",
    }

    return render(request, "blog/trending_posts.html", context)


def featured_posts(request):
    posts_list = Post.objects.filter(status="published", is_featured=True).order_by(
        "-created_at"
    )

    paginator = Paginator(posts_list, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "posts": page_obj,
    }

    return render(request, "blog/featured_posts.html", context)


# Static Pages
def about(request):
    team_members = (
        User.objects.filter(posts__status="published")
        .annotate(post_count=Count("posts", filter=Q(posts__status="published")))
        .filter(post_count__gt=0)
        .distinct()[:6]
    )

    stats = {
        "total_posts": Post.objects.filter(status="published").count(),
        "total_authors": User.objects.filter(posts__status="published")
        .distinct()
        .count(),
        "total_comments": Comment.objects.filter(is_approved=True).count(),
        "total_likes": Like.objects.count(),
        "total_views": sum(
            post.view_count for post in Post.objects.filter(status="published")
        ),
    }

    # Recent activities
    recent_posts = Post.objects.filter(status="published").order_by("-created_at")[:5]
    popular_posts = Post.objects.filter(status="published").order_by("-view_count")[:5]

    return render(
        request,
        "blog/about.html",
        {
            "team_members": team_members,
            "stats": stats,
            "recent_posts": recent_posts,
            "popular_posts": popular_posts,
        },
    )


def contact(request):
    if request.method == "POST":
        # Process contact form
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # Here you would typically send an email or save to database
        # For now, we'll just show a success message

        messages.success(
            request, "📧 Thank you for your message! We'll get back to you soon."
        )
        return redirect("blog:contact")

    return render(request, "blog/contact.html")


# API Views
def api_posts(request):
    posts = Post.objects.filter(status="published").values(
        "id",
        "title",
        "slug",
        "excerpt",
        "featured_image",
        "created_at",
        "author__username",
        "view_count",
        "reading_time",
    )[:10]
    return JsonResponse(list(posts), safe=False)


def api_post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status="published")
    post_data = {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "excerpt": post.excerpt,
        "featured_image": post.featured_image.url if post.featured_image else None,
        "created_at": post.created_at.isoformat(),
        "author": {
            "username": post.author.username,
            "email": post.author.email,
        },
        "view_count": post.view_count,
        "reading_time": post.reading_time,
        "like_count": post.get_like_count(),
        "comment_count": post.comments.count(),
        "tags": list(post.tags.values_list("name", flat=True)),
    }
    return JsonResponse(post_data)


# Newsletter
@require_POST
def subscribe_newsletter(request):
    form = NewsletterSubscriptionForm(request.POST)
    if form.is_valid():
        subscription, created = NewsletterSubscription.objects.get_or_create(
            email=form.cleaned_data["email"], defaults={"is_active": True}
        )

        if not created:
            subscription.is_active = True
            subscription.save()

        return JsonResponse(
            {
                "success": True,
                "message": "🎉 Successfully subscribed to our newsletter!",
            }
        )
    else:
        return JsonResponse({"success": False, "errors": form.errors.get_json_data()})


# System Views
def health_check(request):
    """Simple health check endpoint for monitoring"""
    try:
        # Check database connection
        Post.objects.first()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return JsonResponse(
        {
            "status": "ok",
            "timestamp": timezone.now().isoformat(),
            "database": db_status,
        }
    )


# Homepage View
class HomeView(TemplateView):
    template_name = "blog/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Featured content
        context["featured_posts"] = Post.objects.filter(
            status="published", is_featured=True
        )[:3]
        context["recent_posts"] = Post.objects.filter(status="published").order_by(
            "-created_at"
        )[:6]
        context["popular_posts"] = Post.objects.filter(status="published").order_by(
            "-view_count"
        )[:3]
        context["trending_posts"] = Post.objects.filter(
            status="published", created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by("-view_count")[:3]

        # Statistics for homepage
        context["total_posts"] = Post.objects.filter(status="published").count()
        context["total_authors"] = (
            User.objects.filter(posts__status="published").distinct().count()
        )
        context["total_comments"] = Comment.objects.filter(is_approved=True).count()

        return context


# Error Handler Views
def handler404(request, exception):
    return render(request, "blog/404.html", status=404)


def handler500(request):
    return render(request, "blog/500.html", status=500)


def handler403(request, exception):
    return render(request, "blog/403.html", status=403)


def handler400(request, exception):
    return render(request, "blog/400.html", status=400)


def documentation(request):
    return render(request, "blog/documentation.html")
