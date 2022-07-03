from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):

        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
        help_text = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Никнэйм',
            'email': 'Электронная почта',
        }
