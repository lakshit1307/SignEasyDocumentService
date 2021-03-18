from documentController.models import Document,DocumentPermissions
from rest_framework import serializers

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    ownerId = serializers.StringRelatedField()
    class Meta:
        model = Document
        fields = ['documentId', 'docName', 'docPath', 'ownerId']

class DocumentRequestSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Document
        fields = ['docName', 'ownerId', 'docPath']
