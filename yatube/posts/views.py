from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from posts.models import Group, Post, User, Follow
from posts.forms import CommentForm, PostForm
from posts.utils import paginate


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница сайта."""
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group', 'author')
    page_obj = paginate(request, post_list)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    """Шаблон странницы с постами группы."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = paginate(request, post_list)
    context = {
        'page_obj': page_obj,
        'group': group,
    }

    return render(request, template, context)


def profile(request, username):
    """Шаблон страницы пользователя"""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    page_obj = paginate(request, author.posts.select_related('group').all())
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    """Шаблон страницы поста"""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related(
        'group', 'author'), pk=post_id)
    context = {
        'post': post,
        'form': CommentForm(request.POST or None),
        'comments': post.comments.select_related('author').all(),
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Шаблон коментирования"""
    post = get_object_or_404(Post.objects.select_related(
        'group', 'author'), pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    """Шаблон для  страницы создания поста"""
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', username=request.user.username)

    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Шаблон страницы для редактирования поста"""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post.objects.select_related(
        'group', 'author'), pk=post_id)
    if post.author != request.user:

        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }

    return render(request, template, context)


@login_required
def follow_index(request):
    """Шаблон страницы подписок на авторов"""
    template = 'posts/follow.html'
    authors = request.user.follower.values_list('author', flat=True)
    following_posts = Post.objects.filter(
        author__in=authors).select_related('author', 'group').all()
    page_obj = paginate(request, following_posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Шаблон подписывания на автора"""
    if request.user != User.objects.get(username=username) and not Follow.objects.filter(
        user=request.user, author=User.objects.get(username=username)).exists():
        Follow(user=request.user,
            author=User.objects.get(username=username)).save()
        return redirect('posts:profile', username=username)
    return redirect('posts:index')


@login_required
def profile_unfollow(request, username):
    """Шаблон отписывания от автора"""
    unfollow = Follow.objects.get(user=request.user,
                                  author=User.objects.get(username=username))
    unfollow.delete()
    return redirect('posts:profile', username=username)
