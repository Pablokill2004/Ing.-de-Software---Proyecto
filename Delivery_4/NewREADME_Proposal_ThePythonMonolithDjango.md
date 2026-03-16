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


## Notas adicionales
Para cumplir con los estándares de ingeniería avanzada, el entorno se ha automatizado completamente. No necesitas instalar Python ni bases de datos localmente.