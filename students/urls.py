from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # CORE AUTHENTICATION & NAVIGATION
    # ==========================================
    path('', views.home, name='home'),
    path('register/', views.register_student, name='register_student'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ==========================================
    # DASHBOARDS
    # ==========================================
    path('student_home/', views.student_home, name='student_home'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # ==========================================
    # PAYMENT & VERIFICATION SYSTEM
    # ==========================================
    # 1. Show Bank Details First
    path('payment/instructions/', views.payment_instructions, name='payment_instructions'),
    
    # 2. Student side: Upload transfer evidence
    path('payment/submit/', views.submit_payment, name='submit_payment'),
    
    # 3. Fin Sec / President side: Approve after checking bank app
    path('payment/approve/<int:payment_id>/', views.approve_payment, name='approve_payment'),
    
    # ==========================================
    # EXECUTIVE MANAGEMENT TOOLS
    # ==========================================
    # President only: Event & Campaign Creation
    path('create_event/', views.create_event, name='create_event'),
    path('event/edit/<int:event_id>/', views.create_event, name='edit_event'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('create_fundraising/', views.create_fundraising, name='create_fundraising'),
    
    # President only: Record Management
    path('delete_student/<int:student_id>/', views.delete_student, name='delete_student'),
    
    # school-autocomplete
    path('school-autocomplete/', views.school_autocomplete, name='school_autocomplete'),
]