from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from .models import MedicalHistory, Patient


class EncryptedFieldTests(TestCase):
    def test_clinical_text_is_encrypted_at_rest(self):
        patient = Patient.objects.create(first_name="Ana", last_name="García")
        MedicalHistory.objects.create(patient=patient, allergies="Penicilina")

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT allergies FROM {MedicalHistory._meta.db_table}")
            raw_value = cursor.fetchone()[0]

        self.assertNotIn("Penicilina", raw_value)
        self.assertEqual(MedicalHistory.objects.get().allergies, "Penicilina")


class PatientViewsTests(TestCase):
    def test_patient_pages_require_login(self):
        response = self.client.get(reverse("patients:list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('patients:list')}")

    def test_search_filters_by_name(self):
        user = get_user_model().objects.create_user("fisio", password="contraseña-segura-123")
        self.client.force_login(user)
        Patient.objects.create(first_name="Ana", last_name="García")
        Patient.objects.create(first_name="Luis", last_name="Pérez")

        response = self.client.get(reverse("patients:list"), {"q": "garc"})

        self.assertContains(response, "Ana García")
        self.assertNotContains(response, "Luis Pérez")
