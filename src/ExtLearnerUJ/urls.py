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

<<<<<<< HEAD
    # Materiały
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/<int:material_id>/',
         views.material_detail, name='material_detail'),
=======
    # Materiały — Sprint 1 + Sprint 2/w1
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/new/', views.material_create, name='material_create'),
    path('materials/<int:material_id>/',
         views.material_detail, name='material_detail'),
    path('materials/<int:material_id>/vote/',
         views.material_vote, name='material_vote'),
    path('materials/<int:material_id>/report/',
         views.report_material, name='report_material'),

    # Moderator — materiały (Sprint 2/w1)
    path('moderator/', views.moderator_dashboard, name='moderator_dashboard'),
    path('moderator/materials/',
         views.moderator_materials_queue, name='moderator_materials_queue'),
    path('moderator/materials/<int:material_id>/verify/',
         views.moderator_verify_material, name='moderator_verify_material'),

    # Moderator — prace pisemne (Sprint 2/w2)
    path('moderator/works/',
         views.moderator_works_queue, name='moderator_works_queue'),
    path('moderator/works/<int:work_id>/reserve/',
         views.moderator_reserve_work, name='moderator_reserve_work'),
    path('moderator/works/<int:work_id>/editor/',
         views.moderator_work_editor, name='moderator_work_editor'),
    path('moderator/reviews/<int:review_id>/marks/',
         views.moderator_add_error_mark, name='moderator_add_error_mark'),
    path('moderator/marks/<int:mark_id>/delete/',
         views.moderator_delete_error_mark, name='moderator_delete_error_mark'),

    # Prace pisemne studenta (Sprint 2/w2)
    path('works/', views.my_works, name='my_works'),
    path('works/new/', views.work_new, name='work_new'),
    path('works/<int:work_id>/payment/',
         views.work_payment, name='work_payment'),
    path('works/<int:work_id>/', views.work_detail, name='work_detail'),

    # Admin panel (Sprint 2/w2)
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/reports/',
         views.admin_reports_queue, name='admin_reports_queue'),
    path('admin-panel/reports/<int:report_id>/',
         views.admin_review_report, name='admin_review_report'),
    path('admin-panel/users/',
         views.admin_users_list, name='admin_users_list'),
    path('admin-panel/users/<str:user_email>/',
         views.admin_user_detail, name='admin_user_detail'),
    path('admin-panel/users/<str:user_email>/unblock/',
         views.admin_unblock_user, name='admin_unblock_user'),

    # Notyfikacje
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/',
         views.notification_mark_read, name='notification_mark_read'),
>>>>>>> sprint-2
]
