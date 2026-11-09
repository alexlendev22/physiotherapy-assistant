from functools import lru_cache

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.db import models


@lru_cache
def _fernet():
    # La primera clave cifra; todas sirven para descifrar (permite rotar claves).
    return MultiFernet([Fernet(key) for key in settings.FIELD_ENCRYPTION_KEYS])


class EncryptedTextField(models.TextField):
    """TextField cifrado en reposo con Fernet.

    El valor se guarda cifrado en la base de datos, así que no se puede
    filtrar, buscar ni ordenar por este campo.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return _fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        return _fernet().decrypt(value.encode()).decode()
