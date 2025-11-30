from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    # Core URLs
    path("", views.PostListView.as_view(), name="post_list"),
    path("home/", views.HomeView.as_view(), name="home"),
    # Post Management URLs - MUST COME BEFORE post/<slug:slug>/
    path("post/new/", views.PostCreateView.as_view(), name="post_create"),
    path("post/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path(
        "post/<slug:slug>/delete/", views.PostDeleteView.as_view(), name="post_delete"
    ),
    # Post Interactions - MUST COME BEFORE post/<slug:slug>/
    path("post/<slug:slug>/comment/", views.add_comment, name="add_comment"),
    path("post/<slug:slug>/like/", views.like_post, name="like_post"),
    path("post/<slug:slug>/like-ajax/", views.ajax_like_post, name="ajax_like_post"),
    # Post Detail URL - SHOULD BE LAST among post/ patterns
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    # Dashboard
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    # Discovery
    path("tag/<slug:tag_slug>/", views.posts_by_tag, name="posts_by_tag"),
    path("search/", views.advanced_search, name="advanced_search"),
    path("user/<str:username>/", views.user_posts, name="user_posts"),
    path("trending/", views.trending_posts, name="trending_posts"),
    path("featured/", views.featured_posts, name="featured_posts"),
    # User Management
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Newsletter
    path(
        "newsletter/subscribe/", views.subscribe_newsletter, name="subscribe_newsletter"
    ),
    # Pages
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("documentation/", views.documentation, name="documentation"),
    # API
    path("api/posts/", views.api_posts, name="api_posts"),
    path("api/posts/<slug:slug>/", views.api_post_detail, name="api_post_detail"),
    # System
    path("health/", views.health_check, name="health_check"),
]

# Error handlers
handler404 = "blog.views.handler404"
handler500 = "blog.views.handler500"
handler403 = "blog.views.handler403"
handler400 = "blog.views.handler400"
