from django.urls import path, include
from . import views

urlpatterns = [
    # Public views
    path('', views.homepage, name='homepage'),
    path('login/', views.my_login, name='my-login'),
    path('logout/', views.user_logout, name='user-logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Profile completion views (require login)
    path('customer-profile/', views.customer_profile, name='customer-profile'),
    path('provider-profile/', views.provider_profile, name='provider-profile'),
    path('set-user-type/', views.set_user_type, name='set-user-type'),

    # django-allauth URLs for social authentication and account management
    path('accounts/', include('allauth.urls')),
    path('redirect-after-login/', views.redirect_after_login, name='redirect-after-login'),

]
