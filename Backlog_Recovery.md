# Backlog Recovery

## Objetivo

Reconstruir el backlog funcional del sistema legacy mediante ingeniería inversa
del código fuente.

Dado que el proyecto no cuenta con documentación funcional ni backlog previo, las historias de usuario fueron inferidas directamente a partir del análisis de la estructura del proyecto, las aplicaciones Django y los endpoints REST implementados.

El objetivo es documentar el comportamiento real del sistema tal como está actualmente implementado.

---

## Metodología

Para recuperar el backlog se siguió el siguiente proceso:

1. Se identificaron las aplicaciones Django en el directorio `conduit/apps`.
2. Se realizó el análisis de los archivos `views.py`, `serializers.py` y `urls.py`.
3. Se mapearon los endpoints REST expuestos por el sistema.
4. Cada capacidad funcional encontrada se tradujo en una Historia de Usuario.
5. Cada historia fue asociada a archivos y endpoints reales para garantizar trazabilidad.

Este enfoque permite que el backlog esté alineado con el comportamiento actual del sistema y no con supuestos teóricos.

---

## Backlog Recuperado – Resumen

| ID | Historia de Usuario | App Django | Endpoint |
|----|---------------------|-----------|----------|
| HU-01 | Registro de usuario | authentication | POST `/api/users` |
| HU-02 | Inicio de sesión | authentication | POST `/api/users/login` |
| HU-03 | Ver perfil de usuario | profiles | GET `/api/profiles/{username}` |
| HU-04 | Seguir / dejar de seguir usuarios | profiles | POST / DELETE `/profiles/{username}/follow` |
| HU-05 | Crear artículo | articles | POST `/api/articles` |
| HU-06 | Listar artículos | articles | GET `/api/articles` |
| HU-07 | Marcar artículo como favorito | articles | POST `/api/articles/{slug}/favorite` |
| HU-08 | Comentar artículo | articles | POST `/api/articles/{slug}/comments` |
| HU-09 | Eliminar comentario | articles | DELETE `/api/articles/{slug}/comments/{id}` |
| HU-10 | Actualizar perfil del usuario | authentication | PUT `/api/user` |

---

## HU-01 – Registro de Usuario

**Historia de Usuario**  
Como usuario nuevo, quiero registrarme con correo electrónico y contraseña para crear una cuenta en la plataforma.

**Descripción Funcional**  
Permite la creación de nuevos usuarios mediante validación de datos
y almacenamiento en base de datos.

**Reglas Identificadas**
- El correo electrónico debe ser único.
- El nombre de usuario debe ser único.
- Se validan los datos mediante serializers antes de persistir.

**Trazabilidad**
- App Django: `authentication`
- Archivos:
  - `conduit/apps/authentication/views.py`
  - `conduit/apps/authentication/serializers.py`
- Endpoint: `POST /api/users`

---

## HU-02 – Inicio de Sesión

**Historia de Usuario**  
Como usuario registrado, quiero iniciar sesión para acceder a funcionalidades protegidas del sistema.

**Descripción Funcional**  
Valida credenciales y genera un token JWT para autenticación basada en token.

**Reglas Identificadas**
- Validación de email y contraseña.
- Generación de token JWT.
- Acceso restringido a endpoints protegidos.

**Trazabilidad**
- App Django: `authentication`
- Archivos:
  - `conduit/apps/authentication/views.py`
- Endpoint: `POST /api/users/login`

---

## HU-03 – Ver Perfil de Usuario

**Historia de Usuario**  
Como usuario, quiero visualizar el perfil público de otros usuarios.

**Descripción Funcional**  
Permite consultar información pública de un usuario específico.

**Reglas Identificadas**
- El perfil puede visualizarse sin autenticación.
- Se muestra información básica del usuario.
- Se indica si el usuario autenticado sigue ese perfil.

**Trazabilidad**
- App Django: `profiles`
- Archivos:
  - `conduit/apps/profiles/views.py`
  - `conduit/apps/profiles/serializers.py`
- Endpoint: `GET /api/profiles/{username}`

---

## HU-04 – Seguir / Dejar de Seguir Usuarios

**Historia de Usuario**  
Como usuario autenticado, quiero seguir o dejar de seguir a otros usuarios.

**Descripción Funcional**  
Permite crear o eliminar una relación de seguimiento entre usuarios.

**Reglas Identificadas**
- Solo usuarios autenticados pueden realizar esta acción.
- La relación se almacena en base de datos.
- No se puede seguir al mismo usuario múltiples veces.

**Trazabilidad**
- App Django: `profiles`
- Archivos:
  - `conduit/apps/profiles/views.py`
- Endpoints:
  - `POST /api/profiles/{username}/follow`
  - `DELETE /api/profiles/{username}/follow`

---

## HU-05 – Crear Artículo

**Historia de Usuario**  
Como usuario autenticado, quiero crear artículos para compartir contenido.

**Descripción Funcional**  
Permite la creación de artículos con título, descripción y contenido.

**Reglas Identificadas**
- Solo usuarios autenticados pueden crear artículos.
- Cada artículo genera un slug único.
- El autor queda asociado al artículo.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
  - `conduit/apps/articles/serializers.py`
- Endpoint: `POST /api/articles`

---

## HU-06 – Listar Artículos

**Historia de Usuario**  
Como usuario, quiero visualizar una lista de artículos disponibles.

**Descripción Funcional**  
Permite obtener una lista paginada de artículos.

**Reglas Identificadas**
- Se pueden aplicar filtros por autor, tag o favoritos.
- Soporta paginación mediante parámetros.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoint: `GET /api/articles`

---

## HU-07 – Marcar Artículo como Favorito

**Historia de Usuario**  
Como usuario autenticado, quiero marcar artículos como favoritos.

**Descripción Funcional**  
Permite agregar o remover un artículo de la lista de favoritos.

**Reglas Identificadas**
- Solo usuarios autenticados pueden marcar favoritos.
- Se actualiza el contador de favoritos del artículo.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoints:
  - `POST /api/articles/{slug}/favorite`
  - `DELETE /api/articles/{slug}/favorite`

---

## HU-08 – Comentar Artículo

**Historia de Usuario**  
Como usuario autenticado, quiero comentar artículos.

**Descripción Funcional**  
Permite agregar comentarios asociados a un artículo específico.

**Reglas Identificadas**
- Solo usuarios autenticados pueden comentar.
- El comentario queda asociado al autor y al artículo.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoint: `POST /api/articles/{slug}/comments`

---

## HU-09 – Eliminar Comentario

**Historia de Usuario**  
Como autor de un comentario, quiero eliminarlo.

**Descripción Funcional**  
Permite eliminar comentarios existentes asociados a un artículo.

**Reglas Identificadas**
- Solo el autor del comentario puede eliminarlo.
- La eliminación es permanente en base de datos.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoint: `DELETE /api/articles/{slug}/comments/{id}`

---

## HU-10 – Actualizar Perfil del Usuario

**Historia de Usuario**  
Como usuario autenticado, quiero actualizar mi información personal.

**Descripción Funcional**  
Permite modificar datos como correo electrónico, username o contraseña.

**Reglas Identificadas**
- Solo el usuario autenticado puede modificar su información.
- Se aplican validaciones mediante serializers.

**Trazabilidad**
- App Django: `authentication`
- Archivos:
  - `conduit/apps/authentication/views.py`
- Endpoint: `PUT /api/user`

---

## Conclusión

Este backlog representa las funcionalidades actualmente implementadas
en el sistema, derivadas directamente del análisis del código fuente.

La documentación generada servirá como base para futuras actividades
de modernización, mejora de seguridad, refactorización e implementación de estándares de ingeniería.
