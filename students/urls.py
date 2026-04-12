from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_student, name='register_student'),
    path('login/', views.login_view, name='login'),
    path('student_home/', views.student_home, name='student_home'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # path('dashboard/', views.dashboard, name='dashboard'),

    path('create_event/', views.create_event, name='create_event'),
    path('create_fundraising/', views.create_fundraising, name='create_fundraising'),
    path('mark_payment/<int:student_id>/', views.mark_payment, name='mark_payment'),
    path('logout/', views.logout_view, name='logout'),

    # DELETE STUDENT
    path('delete_student/<int:student_id>/', views.delete_student, name='delete_student'),
]