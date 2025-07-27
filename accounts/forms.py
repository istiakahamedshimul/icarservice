from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, CustomerProfile, ServiceProviderProfile, Vehicle

class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user

class ServiceProviderRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    business_name = forms.CharField(max_length=100, required=True)
    business_license = forms.CharField(max_length=50, required=True)
    provider_type = forms.ChoiceField(choices=ServiceProviderProfile.PROVIDER_TYPES, required=True)
    description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')

class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_picture')

class ServiceProviderProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_picture')

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ('make', 'model', 'year', 'vehicle_type', 'license_plate', 'color', 'is_primary')
        widgets = {
            'year': forms.NumberInput(attrs={'min': 1900, 'max': 2024}),
        }