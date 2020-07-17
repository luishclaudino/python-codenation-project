from rest_framework import serializers
from api.models import User, Group, Event

class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','password']

class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id','name']

class EventModelSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Event
        fields = ['id','level','title','details', 'origin', 'frequency', 'date', 'shelved', 'user_id', 'group_id']
