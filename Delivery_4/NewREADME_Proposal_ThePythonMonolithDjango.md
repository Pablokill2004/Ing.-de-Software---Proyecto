# Conduit - Django RealWorld App (Modernized)

![Project Status](https://img.shields.io/badge/Status-Stabilized-green)
![DevEx](https://img.shields.io/badge/DevEx-Optimized-blue)

This is a legacy Django application that has been stabilized and containerized as part of a Software Engineering modernization project.

## ¿De qué trata el proyecto?

Es una **implementación backend (API)** del clásico ejemplo **RealWorld “Conduit”** usando **Django + Django REST Framework (DRF)**.

La idea del ecosistema **RealWorld** es que múltiples frameworks implementen **la misma especificación de API**, para que puedas:
- aprender patrones reales (auth, CRUD, paginación, etc.),
- comparar stacks,
- usarlo como base para entrevistas, pruebas técnicas o onboarding.

## Prerrequisitos
Antes de comenzar, asegúrate de tener instalado y configurado:
* **Docker Desktop**: [Descargar aquí](https://www.docker.com/products/docker-desktop/)
* **Docker Daemon**: Asegúrate de que Docker esté **abierto y corriendo** antes de ejecutar los comandos.


##  Quick Start (One-Command Setup)

1. **Clona el Respositorio:**
   ```bash
   git clone https://github.com/gothinkster/django-realworld-example-app.git
   
   cd django-realworld-example-app 
2. **Launch with Docker:**
   ```bash
   docker-compose up --build

3. **You should be able to reach your locally at**

   http://localhost:8000

   
## Notas adicionales
 
### 1. Error 404 "Página no encontrada"
Si ves este error, no te preocupes. Se produce porque este proyecto es exclusivamente una API de backend. No tiene una página web configurada para la URL raíz (http://localhost:8000/).

Como indica el mensaje de error, Django solo tiene rutas configuradas para:

- ^admin/ (http://localhost:8000/admin/)
- ^api/ (Endpoints para la aplicación real)

### 2. Como probar tu API
Para comprobar que funciona correctamente, intente acceder a uno de los endpoints de su API en el navegador, Por ejemplo:

- http://localhost:8000/api/articles

- http://localhost:8000/api/tags

Si accedes a uno de esos enlaces, deberías recibir una respuesta JSON, lo que confirma que tu API de producción está completamente operativa.

### 3. Entorno configurado
Para cumplir con los estándares de ingeniería avanzada, el entorno se ha automatizado completamente. No necesitas instalar Python ni bases de datos localmente.