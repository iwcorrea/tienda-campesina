# Plan de Rollback – Prueba Piloto V2

## Desactivar el acceso a pantallas v2 para todos los usuarios

1. **Opción global:**  
   Cambiar la variable de entorno `VITE_FEATURE_V2_PANTALLAS` a `false` en Render y re-desplegar.  
   Esto apaga todas las pantallas v2 inmediatamente.

2. **Opción por usuario:**  
   Ejecutar el siguiente script SQL (o usar el panel de administración) para desactivar la bandera en usuarios específicos:

   ```sql
   UPDATE usuarios SET features = jsonb_set(features, '{v2_enabled}', 'false') WHERE email = 'usuario@example.com';