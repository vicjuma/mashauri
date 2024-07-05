from . import views
from django.urls import path

urlpatterns = [
    path('', views.user_login, name="login"),
    path('dashboard/msp', views.msp_dashboard, name="msp_dashboard"),
    path('dashboard/fdp', views.fdp_dashboard, name="fdp_dashboard"),
    path('dashboard/ec', views.ec_dashboard, name="ec_dashboard"),
    path('dashboard/ep', views.ep_dashboard, name="ep_dashboard"),
    path('dashboard/support', views.support_dashboard, name="support_dashboard"),
    path('dashboard/dispatch', views.dispatch, name="dispatch"),
    path('logout/', views.logout_user, name='logout'),
]
