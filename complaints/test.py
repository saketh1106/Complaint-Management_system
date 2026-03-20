import os
import django

# ✅ Fix for 'settings are not configured' error
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms_project.settings")
django.setup() 
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Complaint, Organization, Message


class ComplaintSystemTests(TestCase):

    def setUp(self):

        # Create organization
        self.organization = Organization.objects.create(
            name="Test Organization"
        )

        # Create normal user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        # Create staff user
        self.staff = User.objects.create_user(
            username="staffuser",
            password="staffpass123",
            is_staff=True
        )

        # Create admin
        self.admin = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
            email="admin@test.com"
        )

        # Create complaint
        self.complaint = Complaint.objects.create(
            title="Test Complaint",
            description="Test description",
            user=self.user,
            organization=self.organization,
            status="Pending",
            priority="Medium"
        )

    # 1️⃣ Home page test
    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    # 2️⃣ User login test
    def test_user_login(self):
        login = self.client.login(
            username="testuser",
            password="testpass123"
        )
        self.assertTrue(login)

    # 3️⃣ Create complaint test
    def test_create_complaint(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("create_complaint"),
            {
                "title": "New Complaint",
                "description": "Complaint description",
                "priority": "Medium"
            }
        )

        self.assertEqual(response.status_code, 302)

    # 4️⃣ Complaint exists test
    def test_complaint_exists(self):
        complaint = Complaint.objects.filter(
            title="Test Complaint"
        ).exists()

        self.assertTrue(complaint)

    # 5️⃣ Admin dashboard access
    def test_admin_dashboard_access(self):
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get("/admin-dashboard/")
        self.assertEqual(response.status_code, 200)

    # 6️⃣ Staff dashboard access
    def test_staff_dashboard_access(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get("/staff-dashboard/")
        self.assertEqual(response.status_code, 200)

    # 7️⃣ Assign complaint to staff
    def test_assign_staff(self):
        self.client.login(username="admin", password="adminpass123")

        response = self.client.post(
            reverse("assign_staff", args=[self.complaint.id]),
            {
                "staff_id": self.staff.id
            }
        )

        self.assertEqual(response.status_code, 302)

    # 8️⃣ Update complaint status
    def test_update_status(self):
        self.client.login(username="staffuser", password="staffpass123")

        response = self.client.post(
            reverse("update_status", args=[self.complaint.id]),
            {
                "status": "Resolved"
            }
        )

        self.assertEqual(response.status_code, 302)

    # 9️⃣ Complaint detail page
    def test_complaint_detail_view(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("complaint_detail", args=[self.complaint.id])
        )

        self.assertEqual(response.status_code, 200)

    # 🔟 Complaint chat message
    def test_send_message(self):
        self.client.login(username="testuser", password="testpass123")

        self.client.post(
            reverse("complaint_detail", args=[self.complaint.id]),
            {
                "message": "Test message"
            }
        )

        message_exists = Message.objects.filter(
            content="Test message"
        ).exists()

        self.assertTrue(message_exists)

    # 11️⃣ Logout test
    def test_user_logout(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)

    # 12️⃣ Admin dashboard without login
    def test_admin_dashboard_without_login(self):
        response = self.client.get("/admin-dashboard/")
        self.assertNotEqual(response.status_code, 200)

    # 13️⃣ Staff dashboard without login
    def test_staff_dashboard_without_login(self):
        response = self.client.get("/staff-dashboard/")
        self.assertNotEqual(response.status_code, 200)

    # 14️⃣ Create complaint without login
    def test_create_complaint_without_login(self):
        response = self.client.post(
            reverse("create_complaint"),
            {
                "title": "Unauthorized Complaint",
                "description": "Should not create"
            }
        )

        self.assertNotEqual(response.status_code, 200)

    # 15️⃣ Invalid login
    def test_invalid_login(self):
        login = self.client.login(
            username="testuser",
            password="wrongpassword"
        )
        self.assertFalse(login)

    # 16️⃣ Complaint count
    def test_complaint_count(self):
        count = Complaint.objects.count()
        self.assertEqual(count, 1)

    # 17️⃣ Staff cannot access admin dashboard
    def test_staff_cannot_access_admin_dashboard(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get("/admin-dashboard/")
        self.assertNotEqual(response.status_code, 200)

    # 18️⃣ User cannot assign staff
    def test_user_cannot_assign_staff(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("assign_staff", args=[self.complaint.id]),
            {
                "staff_id": self.staff.id
            }
        )

        self.assertNotEqual(response.status_code, 200)

    # 19️⃣ Organization exists
    def test_organization_exists(self):
        org = Organization.objects.filter(name="Test Organization").exists()
        self.assertTrue(org)

    # 20️⃣ Complaint belongs to user
    def test_complaint_user_relationship(self):
        complaint = Complaint.objects.get(title="Test Complaint")
        self.assertEqual(complaint.user.username, "testuser")

    # 21️⃣ Complaint priority
    def test_complaint_priority(self):
        complaint = Complaint.objects.get(title="Test Complaint")
        self.assertEqual(complaint.priority, "Medium")

    # 22️⃣ Complaint default status
    def test_complaint_status_default(self):
        complaint = Complaint.objects.get(title="Test Complaint")
        self.assertEqual(complaint.status, "Pending")

    # 23️⃣ Complaint description saved
    def test_complaint_description(self):
        complaint = Complaint.objects.get(title="Test Complaint")
        self.assertEqual(complaint.description, "Test description")

    # 24️⃣ Staff user exists
    def test_staff_user_created(self):
        staff = User.objects.get(username="staffuser")
        self.assertTrue(staff.is_staff)

    # 25️⃣ Admin user exists
    def test_admin_user_created(self):
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_superuser)

    # 26️⃣ Complaint detail requires login
    def test_complaint_detail_requires_login(self):
        response = self.client.get(
            reverse("complaint_detail", args=[self.complaint.id])
        )

        self.assertNotEqual(response.status_code, 200)

    # 27️⃣ Invalid complaint id
    def test_invalid_complaint_id(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("complaint_detail", args=[999])
        )

        self.assertNotEqual(response.status_code, 200)

    # 28️⃣ Staff view complaint
    def test_staff_view_complaint(self):
        self.client.login(username="staffuser", password="staffpass123")

        response = self.client.get(
            reverse("complaint_detail", args=[self.complaint.id])
        )

        self.assertNotEqual(response.status_code, 200)

    def test_multiple_complaints(self):
        Complaint.objects.create(
            title="Second Complaint",
            description="Another issue",
            user=self.user,
            organization=self.organization,
            status="Pending",
            priority="High"
        )
        count = Complaint.objects.count()
        self.assertEqual(count, 2)

    def test_status_update_saved(self):
        self.complaint.status = "Resolved"
        self.complaint.save()
        updated = Complaint.objects.get(id=self.complaint.id)
        self.assertEqual(updated.status, "Resolved")
    
    def test_priority_update(self):

        self.complaint.priority = "High"
        self.complaint.save()

        updated = Complaint.objects.get(id=self.complaint.id)

        self.assertEqual(updated.priority, "High")

    def test_message_linked_to_complaint(self):

        message = Message.objects.create(
            complaint=self.complaint,
            sender=self.user,
            content="Hello"
        )

        self.assertEqual(message.complaint.id, self.complaint.id)

    def test_user_dashboard_access(self):

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get("/user-dashboard/")

        self.assertEqual(response.status_code, 200)

# ------------------------
# Selenium button click tests
# ------------------------
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import unittest

class ButtonClickTests(unittest.TestCase):
    def setUp(self):
        # Create Chrome options
        options = Options()
        options.add_argument("--headless")  # run browser in background

        # Specify ChromeDriver path
        service = Service("C:/Users/Admin/Downloads/chromedriver-win64 (1)/chromedriver.exe")

        # Create driver with service and options
        self.driver = webdriver.Chrome(service=service, options=options)

        # Open local Django site
        self.driver.get("http://127.0.0.1:8000")

    def test_user_login_button(self):
        driver = self.driver
        user_login_button = driver.find_element(By.ID, "user-login-btn")
        user_login_button.click()
        time.sleep(1)
        self.assertIn("Login", driver.title)

    def test_staff_login_button(self):
        driver = self.driver
        staff_login_button = driver.find_element(By.ID, "staff-login-btn")
        staff_login_button.click()
        time.sleep(1)
        self.assertIn("Login", driver.title)

    def tearDown(self):
        self.driver.quit()
    