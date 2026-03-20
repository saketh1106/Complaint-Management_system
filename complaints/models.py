from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'organization'],
                name='unique_username_org'
            )
        ]


class Complaint(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    )

    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    )
    file = models.FileField(upload_to='complaint_files/', null=True, blank=True)
    complaint_id = models.CharField(max_length=10, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='user_complaints')
    staff = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    is_chat_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='complaints')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    def save(self, *args, **kwargs):
        # Only generate complaint_id if blank
        if not self.complaint_id:
            # Generate a unique ID by checking existing ones
            counter = 1
            while True:
                new_id = f"CMP{counter:03d}"
                if not Complaint.objects.filter(complaint_id=new_id).exists():
                    break
                counter += 1
            self.complaint_id = new_id

        # Disable chat if resolved
        if self.status == "Resolved":
            self.is_chat_active = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_id} - {self.title}"


class Message(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"