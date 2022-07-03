from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Выбор группы',
        }
        help_text = {
            'text': 'Текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        id_for_label = {
            'text': 'id_text',
            'group': 'id_group',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
