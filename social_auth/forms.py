from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from authentication.models import User, CustomerProfile, ProviderProfile

# -----------------------------
# User Registration Form (for User creation with user_type)
# -----------------------------
class UserRegisterForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Provider'),
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email


# -----------------------------
# Customer Profile Form
# -----------------------------
class CustomerRegisterForm(forms.ModelForm):
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    location = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'})
    )

    class Meta:
        model = CustomerProfile
        fields = ['phone', 'location']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        return phone

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if not location:
            raise forms.ValidationError('Location is required.')
        return location


# -----------------------------
# Provider Profile Form
# -----------------------------
class ProviderRegisterForm(forms.ModelForm):
    skills = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Skills'})
    )
    service_area = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service Area'})
    )
    hourly_rate = forms.DecimalField(
        required=True,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hourly Rate'})
    )
    location = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'})
    )

    class Meta:
        model = ProviderProfile
        fields = ['skills', 'service_area', 'hourly_rate', 'location']

    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        if not skills:
            raise forms.ValidationError('Skills are required.')
        return skills

    def clean_service_area(self):
        service_area = self.cleaned_data.get('service_area')
        if not service_area:
            raise forms.ValidationError('Service area is required.')
        return service_area

    def clean_hourly_rate(self):
        hourly_rate = self.cleaned_data.get('hourly_rate')
        if hourly_rate is None or hourly_rate <= 0:
            raise forms.ValidationError('Hourly rate must be a positive number.')
        return hourly_rate

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if not location:
            raise forms.ValidationError('Location is required.')
        return location


# -----------------------------
# Login Form
# -----------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True, 'placeholder': 'Username'})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
