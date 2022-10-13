from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.cache import cache_page

from posts.models import Follow
from posts.models import Group
from posts.models import Post
from posts.models import User
from posts.forms import CommentForm
from posts.forms import PostForm
from posts.utils import func_paginator
from posts.consts import VARIABLE_FOR_CACHE_VALUE


# Функция главной страницы
@cache_page(VARIABLE_FOR_CACHE_VALUE, key_prefix="index_page")
def index(request):
    template = "posts/index.html"
    title = "Главная страница"
    post_list = Post.objects.all()
    context = dict(title=title)
    context.update(func_paginator(post_list, request))

    return render(request, template, context)


# Функция страницы на которой посты отфильтрованы по группам
def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = dict(group=group)
    context.update(func_paginator(post_list, request))

    return render(request, template, context)


# Функция профиля пользователя
def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    posts = author.posts.filter(author=author)
    post_count = posts.count

    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    else:
        following = False

    context = dict(author=author, post_count=post_count, following=following)
    context.update(func_paginator(posts, request))

    return render(request, template, context)


# Функция поста пользователя
def post_detail(request, post_id):
    template = "posts/post_detail.html"
    posts = get_object_or_404(Post, pk=post_id)
    author_name = posts.author
    comments = posts.comments.filter(post_id=post_id)
    post_count = Post.objects.filter(author__username=author_name).count
    form = CommentForm(request.POST)

    context = dict(posts=posts,
                   post_count=post_count,
                   form=form,
                   comments=comments
                   )

    return render(request, template, context)


# Функция создания поста
@login_required
def post_create(request):
    template = "posts/create_post.html"
    if request.method == "POST":
        form = PostForm(
            request.POST,
            files=request.FILES or None
        )
        if not form.is_valid():
            return render(request, template, {"form": form})
        post = form.save(commit=False)
        post.author = request.user
        form.save(request.POST)
        return redirect("posts:profile", request.user)

    form = PostForm()
    return render(request, template, {"form": form})


# Функция редактирования поста
@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template = "posts/create_post.html"

    if post.author != request.user:
        return redirect("posts:post_detail", post_id)

    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)

    context = dict(is_edit=True, form=form)
    return render(request, template, context)


# Функция отправки комментария
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    post = Post.objects.filter(author__following__user=request.user)
    context = dict()
    context.update(func_paginator(post, request))
    return render(request, template, context)


# Функция подписки на автора
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user).exists()
    if follow or request.user == author:
        return redirect("posts:profile", username=username)
    Follow.objects.create(author=author, user=request.user)
    return redirect("posts:profile", username=username)


# Функция отписки на автора
@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user)
    follow.delete()
    return redirect("posts:profile", username=username)
