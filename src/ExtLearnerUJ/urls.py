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
    path('verify-email/resend/',
         views.resend_verification_code, name='resend_verification_code'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/delete/', views.delete_account_view, name='delete_account'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Test diagnostyczny
    path('diagnostic/', views.diagnostic_start, name='diagnostic_start'),
    path('diagnostic/<int:test_id>/', views.diagnostic_test, name='diagnostic_test'),
    path('diagnostic/<int:test_id>/autosave/',
         views.diagnostic_autosave, name='diagnostic_autosave'),
    path('diagnostic/result/<int:result_id>/',
         views.diagnostic_result, name='diagnostic_result'),

    # Materiały — Sprint 1 + Sprint 2/w1
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/new/', views.material_create, name='material_create'),
    path('materials/<int:material_id>/',
         views.material_detail, name='material_detail'),
    path('materials/<int:material_id>/vote/',
         views.material_vote, name='material_vote'),
    path('materials/<int:material_id>/report/',
         views.report_material, name='report_material'),
    path('materials/<int:material_id>/delete/',
         views.material_delete, name='material_delete'),

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
    path('works/<int:work_id>/rate/', views.rate_moderator_view, name='rate_moderator'),

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
    path('notifications/read-all/',
         views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('notifications/<int:notification_id>/read/',
         views.notification_mark_read, name='notification_mark_read'),

    # ---- Sprint 3 ----
    # Symulacja egzaminu z timerem (FR-06)
    path('exam/', views.exam_start, name='exam_start'),
    path('exam/<int:attempt_id>/', views.exam_take, name='exam_take'),
    path('exam/<int:attempt_id>/autosave/',
         views.exam_autosave, name='exam_autosave'),
    path('exam/<int:attempt_id>/submit/',
         views.exam_submit, name='exam_submit'),
    path('exam/<int:attempt_id>/result/',
         views.exam_result, name='exam_result'),

    # Ranking / gamifikacja (FR-07)
    path('ranking/', views.ranking, name='ranking'),

    # Statystyki + raport PDF (UC15)
    path('stats/', views.my_stats, name='my_stats'),
    path('stats/report.pdf', views.learning_report_pdf, name='learning_report_pdf'),

    # Wniosek o rolę moderatora (FR-12 / FR-02)
    path('moderator/apply/', views.apply_moderator, name='apply_moderator'),

    # Panel finansowy moderatora (FR-14)
    path('moderator/earnings/', views.moderator_earnings, name='moderator_earnings'),
    path('moderator/earnings/payout/',
         views.moderator_request_payout, name='moderator_request_payout'),

    # Admin — wnioski moderatorskie i role (FR-12)
    path('admin-panel/applications/',
         views.admin_applications, name='admin_applications'),
    path('admin-panel/applications/<int:application_id>/',
         views.admin_review_application, name='admin_review_application'),
    path('admin-panel/users/<str:user_email>/revoke-moderator/',
         views.admin_revoke_moderator, name='admin_revoke_moderator'),
]
