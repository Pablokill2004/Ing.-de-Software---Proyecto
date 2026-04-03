# Django-realworld-example | Architecture Strategy & DevEx

## *One-Command Setup*

Para esta parte puede ver lo sisguientes archivos [Ver el  file](../sbom.json)

### 1. [Dockerfile](../Dockerfile):
¿Por qué?: El proyecto original dependía de versiones de Python obsoletas que generaban conflictos de compatibilidad en sistemas modernos.

Por lo que se eleccionamos la imagen base `python:3.6-slim`, para resolver un `RuntimeError`  relacionado con la definición de clases en `Django 1.10.5 `cuando se intenta ejecutar en` Python 3.7 `o superior.

### 2. [docker-compose.yml](../docker-compose.yml)
¿Por qué?: Reducimos la carga del desarrollador. En lugar de configurar manualmente bases de datos y variables de entorno, centralizamos la configuración en un solo lugar.

Este archivo define el servicio web, mapea los puertos necesarios y asegura que el volumen de datos esté persistido, garantizando que el entorno sea idéntico para cualquier máquina, sin importar si usa Windows (PowerShell) o Linux/Mac. Véase más sobre este problema en el [IS_OnboardingLog.md](../Delivery_1/IS_OnboardingLog.md)

### 3.  [entrypoint.sh](../entrypoint.sh): Automatización de "Cero Pasos"

¿Por qué?: Se necesitaba que la base de datos estuviera lista inmediatamente después de encender el contenedor.

Por lo que este script ejecuta automáticamente las migraciones (`python manage.py migrate`) antes de iniciar el servidor de desarrollo. 
Asegura compatibilidad universal --> `Dockerfile` invoca este script mediante el comando `sh` --> sin problemas de **permisos de ejecución** en entornos Windows.