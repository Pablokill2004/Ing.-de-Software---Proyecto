# AI-Driven Discovery - Context Map

# Context Map 

## Bounded Contexts

### Authentication
**Responsabilidad:**  
Gestión de identidad y acceso de usuarios.

**Entidad principal:**  
- `User`

**Funcionalidades:**
- Registro
- Login
- Tokens JWT
- Permisos

---

### Profiles
**Responsabilidad:**  
Gestión del perfil público y relaciones sociales.

**Entidad principal:**  
- `Profile`

**Funcionalidades:**
- Seguir / dejar de seguir usuarios
- Biografía
- Imagen de perfil

**Nota:**  
Extiende la información del `User` con datos sociales, pero no maneja autenticación.

---

###  Articles (Core Domain)
**Responsabilidad:**  
Gestión principal del sistema: artículos y comentarios.

**Entidades principales:**
- `Article`
- `Comment`
- `Tag`

**Funcionalidades:**
- CRUD de artículos
- CRUD de comentarios
- Favoritos
- Tags
- Feed personalizado

**Importante:**  
Es el Core Domain porque representa el valor principal del negocio.

---

###  Core / Shared Kernel
**Responsabilidad:**  
Funcionalidad técnica compartida entre contextos.

**Componentes:**
- `TimestampedModel` (`created_at`, `updated_at`)
- Utilidades comunes

**Objetivo:**  
Evitar duplicación de lógica transversal, para centralizar código común que se usa en múltiples partes del sistema para mantener consistencia y reducir mantenimiento.

---

# Relaciones entre Bounded Contexts

| Relación | Tipo de Integración | Justificación |
|----------|--------------------|---------------|
| Profiles  Auth | ACL (Anti-Corruption Layer) | Profiles usa el `User ID` como referencia (1:1) sin depender de la lógica interna de autenticación. |
| Articles  Profiles | Customer / Supplier | Articles necesita al autor. Profiles provee la información y Articles la consume mediante FK hacia `Profile`. |
| Articles  Profiles | Partnership | Relación bidireccional para favoritos (M2M). Ambos contextos comparten información de forma colaborativa. |
| Core  Todos | Shared Kernel | Core provee clases base compartidas (`TimestampedModel`) para reutilización y consistencia. |

# AI-Driven Discovery - Context Map - Diagram

