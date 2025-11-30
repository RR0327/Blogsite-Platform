# <h1 align="center"> Django Blog Project </h1>

A professional and feature-rich blogging platform that provides a complete content management system with modern user interaction and performance-focused features.

## Features

### Core Functionality

- User authentication and authorization
- User profile management
- Create, read, update, and delete blog posts
- Draft and published post status
- Rich text content with featured images
- Automatic slug generation and reading time calculation
- Comment system with threaded replies
- Unique post-like system
- Categorization and tagging
- Search and filtering options

### Dashboard and Analytics

- Author dashboard with post statistics
- Recent activity overview
- Insights on popular posts

### Search and Discovery

- Full-text search
- Filtering by tags, categories, and authors
- Sorting by date, popularity, or views

### UI/UX

- Responsive design
- Modern styling
- Clean typography and layout

## Technology Stack

### Backend

- Django 5.2.8
- SQLite (development)
- Pillow
- django-taggit (Tagging System)

### Frontend

- Bootstrap 5.1.3
- Font Awesome
- Django Templates
- Vanilla JavaScript

### Tools

- Python 3.13.0
- Django static and media handling

## Installation

### Requirements

- Python 3.8 or higher
- pip
- Virtual environment (recommended)

### Setup

```bash
git clone <repository-url>
cd blog_project
```

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create superuser (optional):

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Access the application at:
`http://127.0.0.1:8000/`

## Project Structure

```
blog_project/
├── blog/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── templates/blog/
│   └── migrations/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/
│   └── registration/
├── requirements.txt
└── manage.py
```

## Key Models

### Post

- Title, slug, content, excerpt
- Author relationship
- Featured image
- Status (draft/published)
- Publishing date, views, reading time
- Tags and featured post flag

### Comment

- User and post relationship
- Content and timestamps
- Parent for threaded replies
- Moderation support

### Like

- Unique user-post relation
- Timestamp tracking

### UserProfile

- Bio, profile image, website, location
- User statistics and metadata

## Implementation Highlights

- Class-based views for CRUD
- Custom registration with profile creation
- Password reset functionality
- AJAX-powered likes
- Tag-based organization
- Dashboard analytics
- Search and filtering system

## Configuration

The default development configuration includes:

```python
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
# STATIC_URL = '/static/'
# MEDIA_URL = '/media/'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'blog:dashboard'
LOGOUT_REDIRECT_URL = 'blog:post_list'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Submit a pull request

Follow Django coding standards and provide documentation for new features.

## Credits

Developed by **Md Rakibul Hassan**

CSE Undergraduate | Backend Developer | Robotics and IoT Enthusiast

[LinkedIn](https://www.linkedin.com/in/md-rakibul-hassan-507b00308)
[GitHub](https://github.com/RR0327)

## License

Licensed under the MIT License.

---
