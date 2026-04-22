"""URL-e aplikacji ExtLearnerUJ."""
from django.urls import path

from . import views

urlpatterns = [
    # Strony publiczne
    path('', views.landing, name='landing'),
    path('healthz/', views.healthcheck, name='healthcheck'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Test diagnostyczny
    path('diagnostic/', views.diagnostic_start, name='diagnostic_start'),
    path('diagnostic/<int:test_id>/', views.diagnostic_test, name='diagnostic_test'),
    path('diagnostic/<int:test_id>/autosave/',
         views.diagnostic_autosave, name='diagnostic_autosave'),
    path('diagnostic/result/<int:result_id>/',
         views.diagnostic_result, name='diagnostic_result'),

    # Materiały
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/<int:material_id>/',
         views.material_detail, name='material_detail'),
]
