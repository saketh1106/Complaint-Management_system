from .models import Message

def unread_messages_count(request):
    """
    Returns the count of unread messages for the logged-in user 
    based on their specific role and organization.
    """
    if request.user.is_authenticated:
        # Base filter: same organization, not read yet, and not sent by the current user
        unread_qs = Message.objects.filter(
            complaint__organization=request.user.organization,
            is_read=False
        ).exclude(sender=request.user)

        if request.user.is_superuser:
            # Admin sees all unread in their org
            count = unread_qs.count()
        elif request.user.is_staff:
            # Staff sees only unread for tickets assigned to them
            count = unread_qs.filter(complaint__staff=request.user).count()
        else:
            # Regular users see only unread for their own tickets
            count = unread_qs.filter(complaint__user=request.user).count()
            
        return {'unread_chats_count': count}
    
    # If not logged in, return 0
    return {'unread_chats_count': 0}