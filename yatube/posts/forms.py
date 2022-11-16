from django import forms

from .models import Comments, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': "Пост",
            'group': "Группа",
        }
        help_texts = {
            'text': "Новый пост",
            'group': "Группа с новым постом",
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
