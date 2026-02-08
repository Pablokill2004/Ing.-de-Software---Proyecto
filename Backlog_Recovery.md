# **Backlog recovery**

## Objetivo

Reconstruir el backlog funcional del sistema legacy con ingeniería inversa
del código.

Como el proyecto no tiene documentación funcional ni backlog previo,
las historias de usuario fueron inferidas directamente del análisis del código
fuente.

## Metodología

Para recuperar el backlog se siguió el siguiente proceso:

1. Se indentificaron las aplicaciones Django en el directorio `conduit/apps`.
2. Se procedio con el analisis de los archivos `views.py`, `serializers.py` y `urls.py`.
3. Se realizo el mapeo de los  endpoints REST.
4. Cada una de la capacidades se tradujeron en una Historia de Usuario.
5. Se asocian cada una de las historias con archivos y los edpoint reales

Esto con el objetivo de poder realizar el blocklog en relacion al comportamiento real del sistema.

## Backlog Recuperado – Resumen

| ID | Historia de Usuario | App Django | Endpoint |
|----|---------------------|-----------|----------|
| HU-01 | Registro de usuario | autenticación | POST `/api/users` |
| HU-02 | Inicio de sesión | autenticación | POST `/api/users/login` |
| HU-03 | Ver perfil de usuario | perfiles | GET `/api/profiles/{username}` |
| HU-04 | Seguir / dejar de seguir usuarios | perfiles | POST / DELETE `/profiles/{username}/follow` |
| HU-05 | Crear artículo | articulos | POST `/api/articles` |
| HU-06 | Listar artículos | articles | GET `/api/articles` |
| HU-07 | Marcar artículo como favorito | articulos | POST `/api/articles/{slug}/favorite` |
| HU-08 | Comentar artículo | articulos | POST `/api/articles/{slug}/comments` |
| HU-09 | Eliminar comentario | articulos | DELETE `/comments/{id}` |
| HU-10 | Actualizar perfil del usuario | autenticación | PUT `/api/user` |


## HU-01 – Registro de Usuario

**Historia de Usuario**  
Como usuario nuevo, quiero registrarme con correo electrónico y contraseña
para crear una cuenta en la plataforma.

**Trazabilidad**
- App Django: `authentication`
- Archivos:
  - `conduit/apps/authentication/views.py`
  - `conduit/apps/authentication/serializers.py`
- Endpoint: `POST /api/users`


## HU-02 – Inicio de Sesión

**Historia de Usuario**  
Como usuario registrado, quiero iniciar sesión para acceder a funcionalidades
protegidas del sistema.

**Trazabilidad**
- App Django: `authentication`
- Archivos:
  - `conduit/apps/authentication/views.py`
- Endpoint: `POST /api/users/login`


## HU-03 – Ver Perfil de Usuario

**Historia de Usuario**  
Como usuario, quiero visualizar el perfil público de otros usuarios para conocer
su información básica.

**Trazabilidad**
- App Django: `profiles`
- Archivos:
  - `conduit/apps/profiles/views.py`
  - `conduit/apps/profiles/serializers.py`
- Endpoint: `GET /api/profiles/{username}`


## HU-05 – Crear Artículo

**Historia de Usuario**  
Como usuario autenticado, quiero crear artículos para compartir contenido con
otros usuarios.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
  - `conduit/apps/articles/serializers.py`
- Endpoint: `POST /api/articles`


## HU-06 – Listar Artículos

**Historia de Usuario**  
Como usuario, quiero visualizar una lista de artículos para explorar el
contenido disponible.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoint: `GET /api/articles`


## HU-07 – Marcar Artículo como Favorito

**Historia de Usuario**  
Como usuario autenticado, quiero marcar artículos como favoritos para
guardarlos y consultarlos luego.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoints:
  - `POST /api/articles/{slug}/favorite`
  - `DELETE /api/articles/{slug}/favorite`

## HU-08 – Comentar Artículo

**Historia de Usuario**  
Como usuario autenticado, quiero comentar artículos para interactuar con otros
usuarios.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoint: `POST /api/articles/{slug}/comments`


## HU-09 – Eliminar Comentario

**Historia de Usuario**  
Como autor de un comentario, quiero eliminarlo si ya no deseo que esté visible.

**Trazabilidad**
- App Django: `articles`
- Archivos:
  - `conduit/apps/articles/views.py`
- Endpoint: `DELETE /api/articles/{slug}/comments/{id}`


## HU-10 – Actualizar Perfil del Usuario

**Historia de Usuario**  
Como usuario autenticado, quiero actualizar mi información personal.

**Trazabilidad**
- App Django: `authentication`
- Archivos:
  - `conduit/apps/authentication/views.py`
- Endpoint: `PUT /api/user`


Este backlog representa las funcionalidades que podria llegar a presentar el sistema actualmente, a partir del análisis del código fuente, esto ayudara para futuras actualizaciones, mejoras de seguridad o implementación de estandares
