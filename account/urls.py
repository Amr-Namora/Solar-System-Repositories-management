from django.urls import path
from . import views
from .views import MyTokenObtainPairView

urlpatterns = [
    # path('signup/', views.SignUpView.as_view(), name='signup'),

    path('signup/', views.UserSignUpView.as_view(), name='signup'),
    path('users/', views.users, name='users'),
    path('users_no_boss/', views.users_no_boss, name='users_no_boss'),
    path('users_workshops/', views.users_workshops, name='users_workshops'),
    path('profile/', views.profile, name='profile'),
  
    path('stores/', views.stores, name='stores'),
    path('addStores/', views.addStores, name='addStores'),
    path('logout/', views.logout_view.as_view(),name='logout'),
    path('account/me/', views.current_user, name='current_user'),
    path('account/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/<int:user_id>/delete/', views.UserDeleteView.as_view(), name='delete-user'),
    path('stores_toggle_status/', views.storesToggleStatusView, name='stores-user'),
    path('users/<int:user_id>/toggle-status/', views.UserToggleStatusView.as_view(), name='toggle-user-status'),
path('users/<int:user_id>/update/', views.UserUpdateView.as_view(), name='update-user'),
path('UpdatePassword/', views.UpdatePassword, name='UpdatePassword'),

    # path('userinfo/', views.current_user,name='user_info'),
    # path('userinfo/update/', views.update_user,name='update_user'),
    # path('forgot_password/', views.forgot_password,name='forgot_password'),
    # path('reset_password/<str:token>', views.reset_password,name='reset_password'),
]