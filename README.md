# Physiotherapy Assistant

Asistente para fisioterapeutas: agenda, fichas de pacientes con historial clínico cifrado y enlaces de invitación para que los pacientes reserven cita.

**Stack:** Python 3.12+, Django 5.2, SQLite en desarrollo y PostgreSQL en producción, Bootstrap 5 y FullCalendar (los dos últimos desde CDN).

## Puesta en marcha (Windows)

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Genera las claves y pégalas en .env:
python -c "import secrets; print(secrets.token_urlsafe(50))"                        # DJANGO_SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # FIELD_ENCRYPTION_KEYS

python manage.py makemigrations patients scheduling booking
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Después abre http://localhost:8000 e inicia sesión.

Para tener datos de ejemplo (usuario `fisio` / `fisio1234`, horario, pacientes, citas e invitación):

```powershell
python manage.py seed_demo
```

Primeros pasos en la app:
1. **Horario**: configura tus franjas de trabajo. Sin horario no se ofrecen huecos para reservar.
2. **Pacientes**: crea fichas y rellena el historial clínico.
3. **Invitaciones**: crea un enlace y envíalo por WhatsApp o email.

Tests:

```powershell
python manage.py test
```

## Estructura

```
config/              Settings, URLs raíz, WSGI/ASGI
apps/
  core/              Utilidades comunes: campo cifrado, mixins de formularios, modelo base
  patients/          Pacientes, historial clínico (anamnesis), notas de sesión SOAP
  scheduling/        Citas, horario laboral, bloqueos, cálculo de disponibilidad (services.py)
  booking/           Invitaciones y página pública de reserva /reservar/<token>/
templates/           Plantillas HTML por app
static/              CSS propio
```

## Seguridad y RGPD

- Todo exige iniciar sesión (`LoginRequiredMiddleware`), salvo la página pública de reserva.
- Los campos clínicos (historial y notas de sesión) se guardan **cifrados** con Fernet (`apps/core/fields.py`).
  **Guarda `FIELD_ENCRYPTION_KEYS` en un lugar seguro**: si la pierdes, esos datos son irrecuperables.
  Esos campos no se pueden usar en búsquedas ni filtros.
- Los enlaces de invitación usan tokens aleatorios, caducan y tienen un límite de usos.
- Se registra el consentimiento RGPD del paciente, con su fecha.
- Los pacientes se **archivan** en lugar de borrarse, porque la historia clínica debe conservarse durante años.

## Pendiente / ideas

- Registro de auditoría (quién consulta o modifica cada ficha).
- Recordatorios automáticos por email o SMS 24 h antes de la cita.
- Cancelación o cambio de cita por el propio paciente desde un enlace.
- Restricción de solapes en base de datos (`ExclusionConstraint` en PostgreSQL).
- Adjuntar documentos (informes, pruebas de imagen).
- Varios fisioterapeutas o salas.





comprobar que no se puedan hacer dobles citas 
hacer mas grande nombre del paciente en citas

firma digital + consentiments informats