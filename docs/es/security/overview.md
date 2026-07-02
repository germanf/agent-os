# Seguridad

## Autenticación

La autenticación HTTP Basic se aplica a nivel de aplicación:

- **Credenciales**: Variables de entorno `DASH_USER` y `DASH_PASS`, o `dashboard/.credentials.json`
- **Almacenamiento**: Archivos en gitignore con permisos `chmod 0600`
- **Comparación**: Segura contra timing attacks via `hmac.compare_digest()`
- **Excepción**: `/api/health` es accesible sin autenticación

## Seguridad de Red

- **VPN-only**: nginx permite tráfico solo desde la subred `10.0.0.0/24`
- **Firewall**: Reglas iptables persistidas via netfilter-persistent
- **TLS**: Certificado autofirmado para HTTPS; reemplazar con certificado CA para acceso público
- **HSTS**: Header `Strict-Transport-Security` con `max-age=31536000`

## Gestión de Secretos

- Los archivos de credenciales (`.credentials.json`, `.env`) están en gitignore
- Los secretos de API se muestran como `••••••••` en las respuestas GET
- Los endpoints POST preservan valores existentes cuando se envían valores enmascarados
- Nunca hardcodees credenciales en archivos fuente
- Nunca loguees valores de credenciales

## Prevención XSS

- Todo el contenido Markdown renderizado se sanitiza via **DOMPurify**
- `rel="noopener noreferrer"` forzado en todos los enlaces `target="_blank"`
- Lista blanca estricta de etiquetas y atributos HTML

## Seguridad de Subida de Archivos

- Tamaño máximo: 10 MB por archivo
- Máximo total: 50 MB en todos los archivos de una solicitud
- Cantidad máxima: 10 archivos por solicitud
- Validado por FastAPI antes del almacenamiento
- `client_max_body_size` de nginx configurado a 55 MB

## Rate Limiting

- Cada endpoint de API tiene un límite por minuto
- Límites típicos: 30/min para lecturas, 10/min para mutaciones
- Health check: 60/min
- Previene abusos y ataques de fuerza bruta

## Divulgación Responsable

Si descubrís una vulnerabilidad de seguridad, abrí un issue en GitHub con la etiqueta `security`. No divulges vulnerabilidades públicamente hasta que hayan sido abordadas.

## Recomendaciones

1. Usá contraseñas fuertes (32+ caracteres recomendado para instancias expuestas a internet)
2. Rotá las credenciales regularmente
3. Mantené la restricción VPN-only en producción
4. Reemplazá el certificado TLS autofirmado por uno firmado por CA para acceso público
5. Actualizá las dependencias regularmente
6. Monitoreá `/api/alerts` para alertas relacionadas con seguridad
