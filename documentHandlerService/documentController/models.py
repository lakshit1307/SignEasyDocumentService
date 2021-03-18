from django.db import models


class DocUser(models.Model):
    userId = models.AutoField(primary_key=True)
    userName = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = "Doc_User"

    def __str__(self):
        return str(self.userId)


class Document(models.Model):
    documentId = models.AutoField(primary_key=True)
    docName = models.CharField(max_length=200)
    docPath = models.CharField(max_length=200)
    ownerId = models.ForeignKey(DocUser, on_delete=models.CASCADE, db_column='ownerId')

    class Meta:
        db_table = "Document"


class DocumentPermissions(models.Model):
    permissionId = models.AutoField(primary_key=True)
    userId = models.ForeignKey(DocUser, on_delete=models.CASCADE, db_column='userId')
    documentId = models.ForeignKey(Document, on_delete=models.CASCADE, db_column='documentId')

    class Meta:
        db_table = "DocumentPermissions"
        constraints = [
            models.UniqueConstraint(fields=['userId', 'documentId'], name='unique permission')
        ]


class DocumentEdits(models.Model):
    docEditId = models.AutoField(primary_key=True)
    userId = models.ForeignKey(DocUser, on_delete=models.CASCADE, db_column='userId')
    documentId = models.ForeignKey(Document, on_delete=models.CASCADE, db_column='documentId')
    editIsValid = models.BooleanField(db_column='editIsValid', default=True, blank=False, null=False)

    class Meta:
        db_table = "DocumentEdits"
        constraints = [
            models.UniqueConstraint(fields=['userId', 'documentId'], name='unique edits')
        ]
