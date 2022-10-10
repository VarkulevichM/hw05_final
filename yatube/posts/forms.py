from django import forms
from . models import Comment
from . models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {
            "text": "Текст поста",
            "group": "Группа",
            "image": "Выберите изображение",

        }
        help_texts = {
            "text": "Текст нового поста",
            "group": "Группа, к которой будет относиться пост",
            "image": "Загрузите изображение"
        }

    def clean_text(self):
        data = self.cleaned_data["text"]
        if len(data) == 0:
            raise forms.ValidationError("Заполните это поле")
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {
            "text": "Текст комментария",
        }
        help_texts = {
            "text": "Текст нового комментария"
        }
