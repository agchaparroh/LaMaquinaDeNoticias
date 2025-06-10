# 🛡️ Configuración de Seguridad - Supabase
## Máquina de Noticias

Esta guía cubre la configuración de seguridad específica para Supabase después de implementar la base de datos.

## 🔐 Setup Inicial de Seguridad

### 1. Configuración de Proyecto Supabase

```bash
# 1. Crear proyecto en https://supabase.com
# 2. Configurar región (recomendado: más cercana a usuarios)
# 3. Configurar plan (Pro recomendado para producción)
```

### 2. Configuración de Base de Datos

```sql
-- Ejecutar después de las migraciones principales
-- Crear usuario específico para aplicación (recomendado)
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure-app-password';

-- Otorgar permisos básicos
GRANT CONNECT ON DATABASE postgres TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;

-- Permisos específicos para tablas principales
GRANT SELECT, INSERT, UPDATE ON TABLE hechos TO app_user;
GRANT SELECT, INSERT, UPDATE ON TABLE entidades TO app_user;
GRANT SELECT, INSERT, UPDATE ON TABLE articulos TO app_user;
GRANT SELECT ON TABLE hilos_narrativos TO app_user;

-- Permisos para vistas materializadas
GRANT SELECT ON TABLE resumen_hilos_activos TO app_user;
GRANT SELECT ON TABLE agenda_eventos_proximos TO app_user;

-- Permisos para funciones RPC
GRANT EXECUTE ON FUNCTION insertar_articulo_completo(jsonb) TO app_user;
GRANT EXECUTE ON FUNCTION obtener_info_hilo(integer, boolean, integer) TO app_user;
GRANT EXECUTE ON FUNCTION buscar_entidad_similar(text, text, float) TO app_user;
```

### 3. Row Level Security (RLS) Policies

```sql
-- Habilitar RLS en tablas sensibles
ALTER TABLE hechos ENABLE ROW LEVEL SECURITY;
ALTER TABLE entidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE articulos ENABLE ROW LEVEL SECURITY;

-- Política para usuarios autenticados
CREATE POLICY "authenticated_users_can_read" ON hechos
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "authenticated_users_can_insert" ON hechos
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Política para service_role (sin restricciones)
CREATE POLICY "service_role_all_access" ON hechos
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Repetir para otras tablas según necesidad
```

## 🔑 Variables de Entorno Seguras

### Desarrollo Local

```bash
# .env.local
SUPABASE_PROJECT_URL=https://dev-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiI...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiI...
NODE_ENV=development
```

### Producción

```bash
# Variables en plataforma de deployment (Vercel, Netlify, etc.)
SUPABASE_PROJECT_URL=https://prod-project.supabase.co
SUPABASE_ANON_KEY=production-anon-key
SUPABASE_SERVICE_ROLE_KEY=production-service-key
NODE_ENV=production

# NUNCA hardcodear en código
```

## 🌐 Configuración de Storage

### Buckets de Supabase Storage

```sql
-- Crear bucket para documentos (ejecutar en Supabase Dashboard o SQL Editor)
INSERT INTO storage.buckets (id, name, public)
VALUES ('documentos-maquina-noticias', 'documentos-maquina-noticias', false);

-- Políticas de storage
CREATE POLICY "authenticated_users_can_upload" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'documentos-maquina-noticias' 
        AND auth.role() = 'authenticated'
    );

CREATE POLICY "authenticated_users_can_read" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'documentos-maquina-noticias'
        AND auth.role() = 'authenticated'
    );
```

## 🚫 Configuración de CORS

### En Supabase Dashboard

```
# Settings > API > CORS Origins
http://localhost:3000
http://localhost:3001
https://tu-dominio-produccion.com
```

### Programáticamente

```javascript
// En tu aplicación
const supabase = createClient(
  process.env.SUPABASE_PROJECT_URL,
  process.env.SUPABASE_ANON_KEY,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true
    }
  }
)
```

## 🔒 Configuración de Autenticación

### Configurar Providers (en Dashboard)

```
Authentication > Providers
├── Email (habilitar)
├── Google (opcional)
├── GitHub (opcional)
└── Magic Links (recomendado)
```

### Configurar Email Templates

```html
<!-- Confirmar Email -->
<h2>Confirma tu email</h2>
<p>Haz clic en el siguiente enlace:</p>
<a href="{{ .ConfirmationURL }}">Confirmar Email</a>

<!-- Reset Password -->
<h2>Resetear Contraseña</h2>
<p>Haz clic para resetear:</p>
<a href="{{ .ResetPasswordURL }}">Resetear</a>
```

## 📊 Configuración de API

### Rate Limiting

```
# En Dashboard: Settings > API
Rate Limiting: Habilitado
Requests per minute: 100 (ajustar según necesidad)
```

### API Keys Management

```bash
# Rotar claves regularmente (cada 90 días en producción)
# En Dashboard: Settings > API > Generate new anon key
```

## 🔍 Monitoreo de Seguridad

### Logs de Acceso

```sql
-- Tabla para logging de accesos (opcional)
CREATE TABLE IF NOT EXISTS security_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Trigger para logging automático (ejemplo)
CREATE OR REPLACE FUNCTION log_security_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security_logs (action, table_name, timestamp)
    VALUES (TG_OP, TG_TABLE_NAME, NOW());
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

## ⚠️ Checklist de Seguridad

### Pre-Producción

- [ ] Cambiar todas las contraseñas por defecto
- [ ] Configurar RLS en todas las tablas sensibles
- [ ] Configurar políticas de storage apropiadas
- [ ] Verificar CORS origins
- [ ] Configurar rate limiting
- [ ] Configurar backup automático
- [ ] Configurar alertas de monitoring

### Post-Despliegue

- [ ] Verificar que RLS está funcionando
- [ ] Probar autenticación end-to-end
- [ ] Verificar permisos de usuario
- [ ] Probar políticas de storage
- [ ] Configurar monitoring de logs
- [ ] Documentar credenciales de emergencia

## 🚨 Procedimientos de Emergencia

### Comprometer de Claves

```bash
# 1. Rotar inmediatamente en Supabase Dashboard
# 2. Actualizar variables de entorno en todas las aplicaciones
# 3. Revisar logs de acceso
# 4. Notificar al equipo
```

### Acceso No Autorizado

```sql
-- Revocar permisos inmediatamente
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM suspicious_user;

-- Revisar logs
SELECT * FROM security_logs 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

## 📞 Contactos de Seguridad

```
Security Lead: security@empresa.com
Emergency: +XX-XXXX-XXXX
Supabase Support: https://supabase.com/support
```

---

**⚠️ IMPORTANTE**: Este documento contiene información sensible. Mantener actualizado y con acceso restringido.
