from django.urls import include, path

from rest_framework import routers

from rest_framework.authtoken.views import obtain_auth_token

from api import views

router = routers.DefaultRouter()
router.register(r'groups', views.GroupApiViewSet)
router.register(r'events', views.EventApiViewSet)


urlpatterns = [
    # Rotas padrões
    path('', include(router.urls)),
    # Users routes
    # User login to receive the token
    path('login', views.CustomAuthToken.as_view()),
    # User creation
    path('signup', views.signup_user),
    # Group routes
    # List all events for a specific group
    path('groups/<int:group_id>/events/', views.list_group_events),
    # Delete events
    path('delete/events', views.delete_events),
    # Shelve events
    path('shelve/events', views.shelve_events),
    

]