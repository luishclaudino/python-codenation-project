from django.urls import include, path

from rest_framework import routers

from rest_framework.authtoken.views import obtain_auth_token

from api import views

router = routers.DefaultRouter()
router.register(r'groups', views.GroupApiViewSet)
router.register(r'events', views.EventApiViewSet)


urlpatterns = [
    path('', include(router.urls)),
    # Users routes
    path('login/', views.CustomAuthToken.as_view()),
    path('signup/', views.signup_user),
    # Group routes
    path('groups/<int:group_id>/events/', views.list_group_events),
    path('delete/events/', views.delete_events),
    path('shelve/events/', views.shelve_events),
    

]