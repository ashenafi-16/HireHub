from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from .forms import CustomerRegisterForm, ProviderRegisterForm, LoginForm
from authentication.models import CustomerProfile, ProviderProfile
from authentication.utils import Util

User = get_user_model()

# --------------------
# Home Page View
# --------------------
def homepage(request):
    return render(request, 'crm/index.html')


# --------------------
# Login View
# --------------------
def my_login(request):
    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        auth_login(request, user)

        # Redirect based on profile type and completion status
        if hasattr(user, 'customerprofile') and not user.customerprofile.is_profile_complete:
            return redirect('customer-profile')
        elif hasattr(user, 'providerprofile') and not user.providerprofile.is_profile_complete:
            return redirect('provider-profile')
        elif hasattr(user, 'customerprofile') or hasattr(user, 'providerprofile'):
            return redirect('dashboard')

        # User has no profile yet: redirect to role selection
        return redirect('set-user-type')

    return render(request, 'crm/my-login.html', {'loginform': form})


# --------------------
# Role Selection View
# --------------------
@login_required
def set_user_type(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        user = request.user
        
        if user_type in ['customer', 'provider']:
            user.user_type = user_type
            user.save()
            
            if user_type == 'customer':
                CustomerProfile.objects.get_or_create(user=user)
                messages.success(request, 'Customer profile created. Please verify your email to continue.')
            else:
                # Set provider status and create profile
                user.status = 'pending'
                user.save()
                
                ProviderProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'skills': '',
                        'service_area': '',
                        'hourly_rate': 0.00,
                        'location': '',
                        'is_profile_complete': False
                    }
                )
                
                # Send admin notification
                current_site = get_current_site(request).domain
                admin_url = f'http://{current_site}/admin/authentication/user/{user.id}/change/'
                
                admin_email_data = {
                    'email_body': f"""
                    New Provider Registration

                    A new provider has registered and requires approval:

                    Username: {user.username}
                    Email: {user.email}

                    Please review their profile and approve/reject their registration:
                    {admin_url}

                    Best regards,
                    HireHub System
                    """,
                    'to_email': 'admin@hirehub.com',  # Replace with your admin email
                    'email_subject': 'New Provider Registration - Approval Required'
                }
                Util.send_email(admin_email_data)
                
                # Send provider confirmation
                provider_email_data = {
                    'email_body': f"""
                    Hi {user.username},

                    Thank you for registering as a provider with HireHub. Your account is currently pending admin approval.

                    Once approved, you will be able to:
                    - Complete your provider profile
                    - Set your services and rates
                    - Start receiving service requests

                    We will notify you once your account has been reviewed.

                    Best regards,
                    HireHub Team
                    """,
                    'to_email': user.email,
                    'email_subject': 'Provider Registration - Pending Approval'
                }
                Util.send_email(provider_email_data)
                
                messages.success(request, 'Provider profile created. Please verify your email and wait for admin approval.')
            
            return redirect('account_login')
    
    return render(request, 'crm/choose-role.html')


# --------------------
# Profile Completion Views
# --------------------
@login_required(login_url='my-login')
def customer_profile(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

    if profile.is_profile_complete:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST, instance=profile)
        if form.is_valid():
            form.instance.is_profile_complete = True
            form.save()
            return redirect('dashboard')
    else:
        form = CustomerRegisterForm(instance=profile)

    return render(request, 'crm/customer_profile.html', {'form': form})


@login_required(login_url='my-login')
def provider_profile(request):
    # Get or create provider profile
    profile, created = ProviderProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'skills': '',
            'service_area': '',
            'hourly_rate': 0.00,  # Default value
            'location': '',
            'is_profile_complete': False
        }
    )

    if profile.is_profile_complete:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProviderRegisterForm(request.POST, instance=profile)
        if form.is_valid():
            form.instance.is_profile_complete = True
            form.save()
            return redirect('dashboard')
    else:
        form = ProviderRegisterForm(instance=profile)

    return render(request, 'crm/provider_profile.html', {'form': form})


# --------------------
# Dashboard View
# --------------------
@login_required
def dashboard_view(request):
    return render(request, 'crm/dashboard.html')


# --------------------
# Social Login Redirect View
# --------------------
@login_required
def redirect_after_login(request):
    user = request.user

    # If user has no profile yet, redirect to role selection
    if not hasattr(user, 'customerprofile') and not hasattr(user, 'providerprofile'):
        return redirect('set-user-type')

    # If user has a profile, check completion status
    if hasattr(user, 'customerprofile'):
        if not user.customerprofile.is_profile_complete:
            return redirect('customer-profile')
        return redirect('dashboard')

    elif hasattr(user, 'providerprofile'):
        if not user.providerprofile.is_profile_complete:
            return redirect('provider-profile')
        return redirect('dashboard')

    return redirect('set-user-type')


# --------------------
# Logout View
# --------------------
@login_required(login_url='my-login')
def user_logout(request):
    auth_logout(request)
    return redirect('homepage')
