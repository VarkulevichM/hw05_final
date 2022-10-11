from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    # Страница с группами
    path('group/<slug:slug>/',
         views.group_posts, name='group_list'),
    # Профайл пользователя
    path('profile/<str:username>/',
         views.profile, name='profile'),
    # Страница для просмотра отдельного поста.
    path('posts/<int:post_id>/',
         views.post_detail, name='post_detail'),
    # Страница создания поста.
    path('create/',
         views.post_create, name='post_create'),
    # Страница редактирования поста.
    path('posts/<post_id>/edit/',
         views.post_edit, name='edit_post'),
    # Страница создания комментария.
    path('posts/<int:post_id>/comment/',
         views.add_comment, name='add_comment'),
    # Страница постов авторов на которых есть подписка.
    path('follow/',
         views.follow_index, name='follow_index'),
    # Подписка на автора
    path('profile/<str:username>/follow/',
         views.profile_follow, name='profile_follow'),
    # Отписка от автора
    path('profile/<str:username>/unfollow/',
         views.profile_unfollow, name='profile_unfollow')
]
