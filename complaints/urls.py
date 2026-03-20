# complaints/urls.py

from django.urls import path
from . import views
from django.shortcuts import render
from .models import Complaint, Message, Organization, CustomUser

urlpatterns = [

    # ======================================
    # LOGIN / LOGOUT / REGISTRATION
    # ======================================
    path('', views.login_choice, name='login_choice'),
    path('register/', views.register, name='register'),
    path('superadmin-register/', views.superadmin_register, name='superadmin_register'),
    path('logout/', views.org_logout, name='logout'),

    # Organization-priority login
    path('user-login/', views.org_login, {'user_type': 'user'}, name='user_login'),
    path('staff-login/', views.org_login, {'user_type': 'staff'}, name='staff_login'),

    # ======================================
    # DASHBOARDS
    # ======================================
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # ======================================
    # COMPLAINT MANAGEMENT
    # ======================================
    path('create-complaint/', views.create_complaint, name='create_complaint'),
    path('complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),

    # ======================================
    # STAFF / USER MANAGEMENT
    # ======================================
    path('add-staff/', views.add_staff, name='add_staff'),
    path('staff-management/', views.staff_management, name='staff_management'),
    path('user-management/', views.user_management, name='user_management'),
    path('staff-complaints/<int:staff_id>/', views.staff_complaints_detail, name='staff_complaints_detail'),
    path('user-complaints/<int:user_id>/', views.user_complaints_detail, name='user_complaints_detail'),

    # ======================================
    # ASSIGN STAFF TO COMPLAINT
    # ======================================
    path('assign-staff/', views.assign_staff, name='assign_complaints'),
    
    # ======================================
    # STATUS UPDATE
    # ======================================
    path('update-status/', views.update_status, name='update_status'),
    path('staff-update-status/', views.staff_update_status, name='staff_update_status'),
    path('update-status/<int:complaint_id>/', views.update_status, name='update_status_with_id'),
    # ======================================
    # CHAT
    # ======================================
    path('admin-chat/', views.admin_chat, name='admin_chat'),
    path('staff-chat-list/', views.staff_chat_list, name='staff_chat_list'),
    path("user-chat/", views.user_chat_list, name="user_chat_list"),
    
    # ======================================
    # ADD USER (BY ADMIN)
    # ======================================
    path('add-user/', views.add_user, name='add_user'),

    # ======================================
    # PROFILE & PASSWORD
    # ======================================
    path('user-profile/', views.user_profile, name='user_profile'),
    path('staff-profile/', views.staff_profile, name='staff_profile'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),

    # ======================================
    # REPORTS
    # ======================================
    path('reports/', views.reports, name='reports'),

    # ======================================
    # EXTRA HELPER / UTILITY ROUTES (optional)
    # ======================================
    path('get-user-stats/<int:user_id>/', lambda request, user_id: render(
        request, "complaints/user_stats.html", {
            "user_stats": views.get_user_stats(CustomUser.objects.get(id=user_id), request)
        }
    ), name='get_user_stats'),

    path('get-last-message/<int:complaint_id>/', lambda request, complaint_id: render(
        request, "complaints/last_message.html", {"last_message": views.get_last_message(Complaint.objects.get(id=complaint_id))}
    ), name='get_last_message'),
    path('staff-chat/<int:complaint_id>/', views.staff_chat_detail, name='staff_chat_detail'),

]
