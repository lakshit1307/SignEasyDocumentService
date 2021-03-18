from documentController.models import DocUser
from rest_framework import serializers

class DocUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DocUser
        fields = ['userId', 'userName']

class UserRequestSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DocUser
        fields = ['userName']