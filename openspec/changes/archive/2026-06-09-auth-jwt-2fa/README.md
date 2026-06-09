# auth-jwt-2fa

Auth propio con JWT (access 15 min + refresh rotation), 2FA TOTP opcional, recuperación de contraseña y rate limiting por IP+email. C-03 reemplaza el placeholder de header en 	enant_context_dep por un resolver desde el JWT verificado, define la dependency get_current_user, y crea un modelo uth_user mínimo que C-07 extenderá con PII cifrada. CRITICO: el dominio auth es cimiento de seguridad.
