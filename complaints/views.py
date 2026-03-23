from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm
from .models import Complaint, Message, Organization, CustomUser
from .forms import StaffCreationForm, ComplaintForm, SuperAdminCreationForm
from django.utils.timezone import now
from .forms import UserCreationForm
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.messages import get_messages  # <--- Add this line
# ======================================
# LOGIN CHOICE PAGE
# ======================================
def login_choice(request):
    """
    Login choice page: redirect authenticated users to appropriate dashboards
    """
    storage = get_messages(request)
    for _ in storage:
        pass
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")
        elif request.user.is_staff:
            return redirect("staff_dashboard")
        else:
            return redirect("user_dashboard")
    return render(request, "complaints/login_choice.html")


# ======================================
# USER / STAFF REGISTRATION
# ======================================
def register(request):
    storage = get_messages(request)
    for _ in storage:
        pass
    if request.user.is_authenticated:
        return redirect("login_choice")

    organizations = Organization.objects.all()
    form = None

    if request.method == "POST":
        org_id = request.POST.get("organization")

        if not org_id:
            messages.error(request, "Please select an organization.")
            form = StaffCreationForm(organization=None)
        else:
            selected_org = get_object_or_404(Organization, id=org_id)
            form = StaffCreationForm(request.POST, organization=selected_org)

            if form.is_valid():
                user = form.save(commit=False)

                user.organization = selected_org
                user.is_staff = False        # ✅ FIX
                user.is_superuser = False    # ✅ FIX

                user.save()

                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)

                messages.success(request, f"Account created for {user.username}!")

                return redirect("user_dashboard")

    if form is None:
        form = StaffCreationForm(organization=None)

    return render(request, "complaints/register.html", {
        "form": form,
        "organizations": organizations
    })
# ======================================
# SUPERADMIN REGISTRATION (FIXED WITH AUTO-LOGIN)
# ======================================
def superadmin_register(request):
    """
    Creates the SuperAdmin and Organization, then redirects to Staff Login.
    """
    storage = get_messages(request)
    for _ in storage:
        pass
    # 1. If already logged in, send them away from registration
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")
        return redirect("login_choice")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        org_name = request.POST.get("organization_name")
        secret_key = request.POST.get("secret_key")

        # 2. Validation
        if secret_key != "MYSECRET123":
            messages.error(request, "Invalid secret key!")
            return render(request, "complaints/superadmin_register.html")

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return render(request, "complaints/superadmin_register.html")

        # 3. Create Organization
        organization, created = Organization.objects.get_or_create(name=org_name)

        # 4. Create the SuperAdmin User
        if CustomUser.objects.filter(username=username, organization=organization).exists():
            messages.error(request, "Username already exists in this organization!")
            return render(request, "complaints/superadmin_register.html")

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password1,
            organization=organization
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        # 5. Success Message and Redirect to Staff Login
        messages.success(request, f"Superadmin for {org_name} created! Please login.")
        return redirect("staff_login")

    return render(request, "complaints/superadmin_register.html")

# ======================================
# ORGANIZATION-FIRST LOGIN
# ======================================
from django.contrib import messages
from django.contrib.messages import get_messages
def org_login(request, user_type='user'):
    """
    Priority 1: Organization Scope
    Priority 2: User Validation
    Priority 3: Strict Role-Based Routing
    """
    storage = get_messages(request)
    for _ in storage:
        pass
    # 1. Redirect already logged-in users based on strict hierarchy
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")
        elif request.user.is_staff:
            return redirect("staff_dashboard")
        else:
            return redirect("user_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        org_id = request.POST.get("organization")

        try:
            # 2. Scope the search to the specific Organization selected
            organization = Organization.objects.get(id=org_id)
            
            # 3. Find the user ONLY within this Organization
            # Using .filter().first() prevents MultipleObjectsReturned errors
            user_obj = CustomUser.objects.filter(
                username=username, 
                organization=organization
            ).first()

            if user_obj and user_obj.check_password(password):
                if not user_obj.is_active:
                    messages.error(request, "This account has been disabled.")
                    return redirect("login_choice")

                # 4. PORTAL GUARD: Prevent cross-login between User and Staff portals
                # 'user_type' comes from the URL (user-login/ vs staff-login/)
                if user_type == "staff" and not user_obj.is_staff:
                    messages.error(request, f"Access Denied: {username} is not a staff member of {organization.name}.")
                    return redirect("staff_login")
                
                if user_type == "user" and (user_obj.is_staff or user_obj.is_superuser):
                    messages.error(request, "Staff and Admins must login through the Staff Portal.")
                    return redirect("user_login")

                # 5. AUTHENTICATE
                # Explicitly set the backend to avoid ValueError
                user_obj.backend = 'complaints.backends.OrganizationBackend'
                login(request, user_obj)
                
                # 6. FINAL ROUTING HIERARCHY (Admin check MUST be first)
                if user_obj.is_superuser:
                    return redirect("admin_dashboard")
                elif user_obj.is_staff:
                    return redirect("staff_dashboard")
                else:
                    return redirect("user_dashboard")
            else:
                messages.error(request, f"Invalid credentials for {organization.name}.")

        except Organization.DoesNotExist:
            messages.error(request, "Please select a valid organization.")
        except Exception as e:
            messages.error(request, "An error occurred during login. Please try again.")

    # Get all organizations for the dropdown
    organizations = Organization.objects.all()
    return render(request, f"complaints/{user_type}_login.html", {"organizations": organizations})

def org_logout(request):
    """Logout current user and redirect to login choice page"""
    logout(request)
    return redirect("login_choice")


# ======================================
# DASHBOARDS
# ======================================
@login_required
def user_dashboard(request):
    # 🔐 Role protection
    if request.user.is_superuser:
        return redirect("admin_dashboard")

    if request.user.is_staff:
        return redirect("staff_dashboard")

    # 📊 User complaints (ORG SAFE)
    complaints = Complaint.objects.filter(
        user=request.user,
        organization=request.user.organization
    ).select_related("staff").order_by("-id")

    context = {
        "complaints": complaints,
        "total_complaints": complaints.count(),
        "pending_complaints": complaints.filter(status="Pending").count(),
        "inprogress_complaints": complaints.filter(status="In Progress").count(),
        "resolved_complaints": complaints.filter(status="Resolved").count(),
    }

    return render(request, "complaints/user_dashboard.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):

    # 🔥 BASE QUERY (NO FILTERS)
    all_complaints = Complaint.objects.filter(
        organization=request.user.organization
    )

    # 🔍 FILTERED QUERY
    complaints = all_complaints.select_related("user", "staff").order_by("-id")

    search_query = request.GET.get("search")
    if search_query:
        complaints = complaints.filter(title__icontains=search_query)

    status_filter = request.GET.get("status")
    if status_filter:
        complaints = complaints.filter(status=status_filter)

    priority_filter = request.GET.get("priority")
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter)

    # 📄 PAGINATION
    paginator = Paginator(complaints, 5)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,

        # ✅ GLOBAL COUNTS (NOT FILTERED)
        "total_complaints": all_complaints.count(),
        "pending_complaints": all_complaints.filter(status="Pending").count(),
        "inprogress_complaints": all_complaints.filter(status="In Progress").count(),
        "resolved_complaints": all_complaints.filter(status="Resolved").count(),

        "search_query": search_query,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
    }

    return render(request, "complaints/admin_dashboard.html", context)


@login_required
@user_passes_test(lambda u: u.is_staff and not u.is_superuser)
def staff_dashboard(request):

    assigned_complaints = Complaint.objects.filter(
        staff=request.user,
        organization=request.user.organization   # ✅ FIX
    ).order_by("-id")

    total_count = assigned_complaints.count()
    pending_count = assigned_complaints.filter(status="Pending").count()
    in_progress_count = assigned_complaints.filter(status="In Progress").count()
    resolved_count = assigned_complaints.filter(status="Resolved").count()

    context = {
        "assigned_complaints": assigned_complaints,
        "total_count": total_count,
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "resolved_count": resolved_count,
    }

    return render(request, "complaints/staff_dashboard.html", context)
# ======================================
# COMPLAINT CREATION
# ======================================
@login_required
def create_complaint(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        priority = request.POST.get("priority")
        file = request.FILES.get('file')

        if title and description:
            complaint = Complaint.objects.create(
                title=title,
                description=description,
                priority=priority,
                user=request.user,
                organization=request.user.organization,
                file=file
            )

            # 🔥 AUTO SEND FILE TO CHAT
            if file:
                Message.objects.create(
                    complaint=complaint,
                    sender=request.user,
                    content=f"📎 {file.name}",
                    file=file
                )

            messages.success(request, "Complaint submitted successfully!")
            return redirect("user_dashboard")

        else:
            messages.error(request, "All fields are required!")

    return render(request, "complaints/create_complaint.html")

# ======================================
# ADD STAFF (BY ADMIN)
# ======================================
# complaints/views.py
@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_staff(request):
    admin_org = request.user.organization
    
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 1. Check if username exists in THIS org
        if CustomUser.objects.filter(username=username, organization=admin_org).exists():
            messages.error(request, "This username is already taken in your organization.")
        else:
            # 2. Create the user with explicit flags
            new_staff = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                organization=admin_org
            )
            new_staff.is_staff = True      # This makes them Staff
            new_staff.is_superuser = False # This ensures they are NOT admins
            new_staff.save()
            
            messages.success(request, f"Staff account for {username} created successfully!")
            return redirect("staff_management")

    return render(request, "complaints/add_staff.html")

# ======================================
# STAFF MANAGEMENT 
# ======================================

@login_required
@user_passes_test(lambda u: u.is_superuser)
def staff_management(request):
    # This filter will now show the staff because 'organization' is no longer NULL
    staff_users = CustomUser.objects.filter(
        is_staff=True, 
        is_superuser=False, 
        organization=request.user.organization
    )

    if request.method == "POST":
        staff_ids = request.POST.getlist("delete_staff")
        if staff_ids:
            # Delete only if they belong to this admin's organization
            CustomUser.objects.filter(
                id__in=staff_ids, 
                organization=request.user.organization
            ).delete()
            messages.success(request, "Selected staff deleted.")
            return redirect("staff_management")

    return render(request, "complaints/staff_management.html", {"staff_users": staff_users})
# ======================================
# USER MANAGEMENT
# ======================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_management(request):
    """
    View all users under the superadmin's organization (SECURED)
    """
    normal_users = CustomUser.objects.filter(
        is_staff=False, 
        organization=request.user.organization
    )

    if request.method == "POST":
        user_ids = request.POST.getlist("delete_users")
        if user_ids:
            deleted_count, _ = CustomUser.objects.filter(
                id__in=user_ids, 
                organization=request.user.organization
            ).delete()
            
            messages.success(request, f"{deleted_count} user(s) deleted successfully!")
            return redirect("user_management")

    user_stats = []
    for user in normal_users:
        complaints = Complaint.objects.filter(
            user=user,
            organization=request.user.organization
        ).order_by('-created_at')
        
        last_complaint = complaints.first()
        
        user_stats.append({
            "user": user,
            "total_complaints": complaints.count(),
            "last_complaint_id": last_complaint.id if last_complaint else None,
            "last_complaint_date": last_complaint.created_at if last_complaint else None
        })

    return render(request, "complaints/user_management.html", {"user_stats": user_stats})
# ======================================
# STAFF / USER COMPLAINT DETAILS
# ======================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def staff_complaints_detail(request, staff_id):
    # FIX 2: Secure the User lookup to the Admin's Org
    staff_user = get_object_or_404(
    CustomUser,
    id=staff_id,
    organization=request.user.organization,
    is_staff=True
)
    staff_complaints = Complaint.objects.filter(
        staff=staff_user,
        organization=request.user.organization
    ).order_by('-created_at')
    return render(request, "complaints/staff_complaints_detail.html", {
        "staff": staff_user,
        "staff_complaints": staff_complaints
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_complaints_detail(request, user_id):
    # FIX 3: Secure the User lookup
    user = get_object_or_404(
    CustomUser,
    id=user_id,
    organization=request.user.organization,
    is_staff=False
)
    complaints = Complaint.objects.filter(
        user=user,
        organization=request.user.organization
    ).order_by('-created_at')
    return render(request, "complaints/user_complaints_detail.html", {
        "user": user,
        "complaints": complaints
    })

# ======================================
# ASSIGN STAFF TO COMPLAINT
# ======================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def assign_staff(request):
    complaints = Complaint.objects.filter(
        staff__isnull=True,
        organization=request.user.organization
    ).order_by('-created_at')

    staff_users = CustomUser.objects.filter(
        is_staff=True,
        is_superuser=False,
        organization=request.user.organization
    )

    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        staff_id = request.POST.get("staff_id")
        if complaint_id and staff_id:
            complaint = get_object_or_404(
                Complaint,
                id=complaint_id,
                organization=request.user.organization
            )
            staff_user = get_object_or_404(
                CustomUser,
                id=staff_id,
                organization=request.user.organization
            )

            complaint.staff = staff_user
            complaint.status = "In Progress"
            complaint.assigned_at = timezone.now()
            complaint.save()

            # 🔥 Automatic message for assignment
            Message.objects.create(
                complaint=complaint,
                sender=request.user,
                content=f"Staff {staff_user.username} has been assigned to this complaint."
            )

            messages.success(request, f"{complaint.title} assigned to {staff_user.username}")
            return redirect("assign_complaints")

    return render(request, "complaints/assign_complaints.html", {
        "complaints": complaints,
        "staff_users": staff_users
    })


# ======================================
# STAFF UPDATE STATUS PAGE
# ======================================
@login_required
@user_passes_test(lambda u: u.is_staff and not u.is_superuser)
def staff_update_status(request):
    """
    Staff can update status for complaints assigned to them
    """
    assigned_complaints = Complaint.objects.filter(
        staff=request.user,
        organization=request.user.organization
    ).order_by('-id')

    if request.method == 'POST':
        complaint_id = request.POST.get('complaint_id')
        status = request.POST.get('status')

        if complaint_id and status:
            complaint = get_object_or_404(
                Complaint,
                id=complaint_id,
                staff=request.user,
                organization=request.user.organization
            )

            # Update status metadata
            complaint.status = status
            complaint.updated_at = timezone.now()

            # 🔥 Create automatic chat notification
            Message.objects.create(
                complaint=complaint,
                sender=request.user,
                content=f"Status has been updated to '{status}'."
            )

            # If resolved, lock the chat
            if status == "Resolved":
                complaint.is_chat_active = False

            complaint.save()

            messages.success(request, f"{complaint.title} status updated to {status}")
            return redirect('staff_update_status')

    return render(request, 'complaints/staff_update_status.html', {
        'assigned_complaints': assigned_complaints  
    })
# ======================================
# UPDATE STATUS (ADMIN)
# ======================================
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def update_status(request, complaint_id=None): # Added =None
    """
    Update status of complaint; used by both staff and superadmin
    """
    # If ID is not in URL, look for it in the POST data (from the Modal)
    if not complaint_id:
        complaint_id = request.POST.get("complaint_id")

    if request.user.is_superuser:
        complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
            organization=request.user.organization
        )
    else:
        complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
            staff=request.user,
            organization=request.user.organization
        )

    if request.method == "POST":
        status = request.POST.get("status")
        if status in ["Pending", "In Progress", "Resolved"]:
            complaint.status = status
            complaint.save()
            messages.success(request, f"Complaint {complaint.complaint_id} updated to {status}!")

    return redirect("admin_dashboard") if request.user.is_superuser else redirect("staff_dashboard")
# ======================================
# USER PROFILE
# ======================================
@login_required
def user_profile(request):
    storage = get_messages(request)
    for _ in storage:
        pass
    if request.user.is_superuser:
        return redirect("admin_dashboard")

    if request.user.is_staff:
        return redirect("staff_dashboard")

    password_form = PasswordChangeForm(request.user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            email = request.POST.get("email")
            request.user.email = email
            request.user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("user_profile")

        elif "change_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")
                return redirect("user_profile")
            else:
                messages.error(request, "Please correct the errors below.")

    return render(request, "complaints/user_profile.html", {
        "user": request.user,
        "password_form": password_form
    })


# ======================================
# STAFF PROFILE
# ======================================
@login_required
@user_passes_test(lambda u: u.is_staff and not u.is_superuser)
def staff_profile(request):
    password_form = PasswordChangeForm(request.user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            email = request.POST.get("email")
            request.user.email = email
            request.user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("staff_profile")
        elif "change_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")
                return redirect("staff_profile")
            else:
                messages.error(request, "Please correct the errors below.")

    return render(request, "complaints/staff_profile.html", {"user": request.user, "password_form": password_form, "messages": messages.get_messages(request)})


# ======================================
# ADMIN PROFILE
# ======================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_profile(request):
    password_form = PasswordChangeForm(request.user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            email = request.POST.get("email")
            request.user.email = email
            request.user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("admin_profile")
        elif "change_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")
                return redirect("admin_profile")
            else:
                messages.error(request, "Please correct the errors below.")

    return render(request, "complaints/admin_profile.html", {"user": request.user, "password_form": password_form, "messages": messages.get_messages(request)})


# ======================================
# REPORTS
# ======================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def reports(request):
    """
    Show report stats for complaints (ORG-SAFE)
    """

    # 🔥 FILTER BY ORGANIZATION (MAIN FIX)
    complaints = Complaint.objects.filter(
        organization=request.user.organization
    )

    total = complaints.count()
    pending = complaints.filter(status="Pending").count()
    in_progress = complaints.filter(status="In Progress").count()
    resolved = complaints.filter(status="Resolved").count()

    return render(request, "complaints/reports.html", {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved
    })

# ======================================
# ADMIN CHAT
# ======================================
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count, Q, Max
from .models import Complaint, Message

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_chat(request):
    """
    Admin chat interface for communicating with users via complaints.
    Sorting logic: Unread counts first, then by the most recent message.
    """
    # Base query filtered by the admin's organization
    complaints = Complaint.objects.filter(
        organization=request.user.organization
    ).annotate(
        # Annotate with the number of unseen messages from the user
        unseen_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
        # Annotate with the time of the latest message for sorting
        last_msg_time=Max('messages__timestamp')
    ).order_by('-unseen_count', '-last_msg_time', '-created_at')

    complaint_id = request.GET.get('complaint_id')
    active_complaint = None
    messages_list = []

    if complaint_id:
        active_complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
            organization=request.user.organization
        )

        messages_list = active_complaint.messages.all().order_by('timestamp')

        # Mark unseen messages as read when the admin views the conversation
        messages_list.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        if request.method == "POST":
            # Security check to see if chat is still active
            if not active_complaint.is_chat_active:
                messages.error(request, "Chat is closed (Complaint Resolved)")
                return redirect(f"{reverse('admin_chat')}?complaint_id={active_complaint.id}")

            content = request.POST.get("message")
            uploaded_file = request.FILES.get("file")

            if content or uploaded_file:
                Message.objects.create(
                    complaint=active_complaint,
                    sender=request.user,
                    content=content,
                    file=uploaded_file
                )

            return redirect(f"{reverse('admin_chat')}?complaint_id={active_complaint.id}")

    return render(request, "complaints/admin_chat.html", {
        "complaints": complaints,
        "active_complaint": active_complaint,
        "messages": messages_list
    })

# ======================================
# STAFF CHAT LIST
# ======================================
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.db.models import Count, Q, Max  # Added for sorting and counting
from .models import Complaint, Message

@login_required
@user_passes_test(lambda u: u.is_staff and not u.is_superuser)
def staff_chat_list(request):
    # ✅ Get all assigned complaints, annotate with unseen count, and sort
    # 1. 'unseen_count': counts messages where is_read=False and sender is NOT the staff
    # 2. 'last_msg_time': the time of the latest message
    # 3. Sort by unseen_count (most unread first) and then by time
    assigned_complaints = Complaint.objects.filter(
        staff=request.user,
        organization=request.user.organization
    ).annotate(
        unseen_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
        last_msg_time=Max('messages__timestamp')
    ).order_by('-unseen_count', '-last_msg_time')

    complaint_id = request.GET.get("complaint_id")
    selected_complaint = None
    messages = None

    if complaint_id:
        selected_complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
            staff=request.user,
            organization=request.user.organization
        )

        # ✅ Get all messages
        messages = Message.objects.filter(
            complaint=selected_complaint
        ).order_by("timestamp")

        # ✅ Mark all messages in THIS chat as READ when staff opens it
        messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        # ✅ Handle sending message
        if request.method == "POST" and selected_complaint.is_chat_active:
            content = request.POST.get("message")
            uploaded_file = request.FILES.get("file")
            if content or uploaded_file:
                Message.objects.create(
                    complaint=selected_complaint,
                    sender=request.user,
                    content=content,
                    file=uploaded_file,
                    is_read=False # New messages start as unread
                )

            return redirect(f"{reverse('staff_chat_list')}?complaint_id={complaint_id}")

    return render(request, "complaints/staff_chat_list.html", {
        "user_chats": assigned_complaints,
        "selected_complaint": selected_complaint,
        "messages": messages
    })

# ======================================
# USER CHAT LIST
# ======================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Max
from .models import Complaint, Message

@login_required
def user_chat_list(request):
    # ✅ Added sorting: Unread (from Staff/Admin) first, then by latest message
    complaints = Complaint.objects.filter(
        user=request.user,
        organization=request.user.organization
    ).annotate(
        unseen_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
        last_msg_time=Max('messages__timestamp')
    ).order_by('-unseen_count', '-last_msg_time', '-created_at')

    selected_complaint = None
    messages_list = []
    complaint_id = request.GET.get("complaint_id")

    if complaint_id:
        selected_complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
            user=request.user,
            organization=request.user.organization
        )

        messages_list = selected_complaint.messages.all().order_by("timestamp")

        # ✅ Mark as read when user opens the chat
        messages_list.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        if request.method == "POST":
            if not selected_complaint.is_chat_active:
                messages.error(request, "Chat is closed (Complaint Resolved)")
                return redirect(f"/user-chat/?complaint_id={complaint_id}")

            content = request.POST.get("message")
            uploaded_file = request.FILES.get("file")

            if content or uploaded_file:
                Message.objects.create(
                    complaint=selected_complaint,
                    sender=request.user,
                    file=uploaded_file,
                    content=content,
                    is_read=False # Unread for the staff/admin
                )

            return redirect(f"/user-chat/?complaint_id={complaint_id}")

    return render(request, "complaints/user_chat_list.html", {
        "complaints": complaints,
        "selected_complaint": selected_complaint,
        "messages": messages_list
    })


# ======================================
# ADD USER BY ADMIN
# ======================================
@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_user(request):
    admin_org = request.user.organization

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")

        if CustomUser.objects.filter(username=username, organization=admin_org).exists():
            messages.error(request, f"Username '{username}' already exists.")
        
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")

        else:
            CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                organization=admin_org,
                is_staff=False,
                is_superuser=False
            )

            messages.success(request, f"User '{username}' created successfully!")
            return redirect("user_management")

    return render(request, "complaints/add_user.html")



# ======================================
# HELPER FUNCTION: GET LAST MESSAGE
# ======================================
def get_last_message(complaint):
    """
    Utility function to fetch the last message of a complaint
    """
    last_msg = complaint.messages.order_by("-timestamp").first()
    if last_msg:
        return {"content": last_msg.content, "timestamp": last_msg.timestamp}
    return {"content": "No messages yet", "timestamp": None}


# ======================================
# HELPER FUNCTION: CHECK STAFF ASSIGNED
# ======================================
def is_staff_assigned(complaint, staff_user):
    """
    Returns True if the complaint is assigned to given staff_user
    """
    return complaint.staff == staff_user

# ======================================
# STAFF DETAIL VIEW FOR EACH COMPLAINT
# ======================================
@login_required
def complaint_detail(request, complaint_id):
    complaint = get_object_or_404(
        Complaint, 
        id=complaint_id, 
        organization=request.user.organization
    )

    # Permission check
    if not (complaint.user == request.user or request.user.is_superuser or complaint.staff == request.user):
        messages.error(request, "Access denied.")
        return redirect("login_choice")

    if request.method == "POST":
        content = request.POST.get("message")
        uploaded_file = request.FILES.get("file")
        if uploaded_file:
            complaint.file = uploaded_file  # attach the file directly to the complaint
        complaint.save()
        if content or uploaded_file:
            Message.objects.create(complaint=complaint, sender=request.user, content=content,file=uploaded_file)
            return redirect("complaint_detail", complaint_id=complaint.id)

    messages_list = complaint.messages.all().order_by("timestamp")

    # 🔥 Pass base template name to the template
    if request.user.is_superuser:
        base_template = "complaints/base_admin.html"
    elif request.user.is_staff:
        base_template = "complaints/base_staff.html"
    else:
        base_template = "complaints/base.html"

    return render(request, "complaints/complaint_detail.html", {
        "complaint": complaint,
        "messages": messages_list,
        "base_template": base_template
    })


# ======================================
# EXPLICIT HELPER FUNCTION: GET USER STATS
# ======================================
def get_user_stats(user, request):
    """
    Return dict with user complaint stats - FIXED with request scope
    """
    complaints = Complaint.objects.filter(
        user=user, 
        organization=request.user.organization
    )
    last_complaint = complaints.order_by("-created_at").first()
    return {
        "user": user,
        "total_complaints": complaints.count(),
        "last_complaint_id": last_complaint.id if last_complaint else None,
        "last_complaint_date": last_complaint.created_at if last_complaint else None
    }

# complaints/views.py
@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_chat_detail(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id, staff=request.user)
    messages_list = Message.objects.filter(complaint=complaint).order_by('timestamp')

    if request.method == "POST":
        content = request.POST.get("message")
        uploaded_file = request.FILES.get("file")
        if content or uploaded_file:
            if complaint.is_chat_active:  
                Message.objects.create(
                    sender=request.user,
                    complaint=complaint,
                    file=uploaded_file,
                    content=content
                )
                return redirect("staff_chat_detail", complaint_id=complaint.id)
            else:
                messages.error(request, "Chat is closed for this complaint.")

    return render(request, "complaints/staff_chat_detail.html", {
        "complaint": complaint,
        "messages": messages_list
    })
