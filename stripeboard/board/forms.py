from django import forms
from django.contrib.auth.models import User

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from crispy_forms.bootstrap import FormActions


class UserCreateForm(forms.Form):
    email = forms.EmailField(max_length=120)
    password = forms.CharField(max_length=120, widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError('That email already exists in our system.')
        return email

    def create_user(self):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        return User.objects.create_user(email, email, password)

    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.layout = Layout(
        Field('email', css_class='input-xlarge'),
        Field('password', css_class='input-xlarge'),
        FormActions(
            Submit('submit', 'Submit', css_class='btn-primary')
        )
    )
