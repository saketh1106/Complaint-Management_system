# complaints/admin.py
from django.contrib import admin
from .models import Organization, Complaint, Message

# ======================================
# ORGANIZATION ADMIN
# ======================================
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)
    ordering = ('id',)


# ======================================
# COMPLAINT ADMIN
# ======================================
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_id', 'title', 'user', 'staff', 'status', 'priority', 'organization', 'created_at')
    list_filter = ('status', 'priority', 'organization')
    search_fields = ('complaint_id', 'title', 'user__username', 'staff__username')
    ordering = ('-created_at',)


# ======================================
# MESSAGE ADMIN
# ======================================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint', 'sender', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('content', 'sender__username', 'complaint__complaint_id')
    ordering = ('-timestamp',)

    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = "Message Content"