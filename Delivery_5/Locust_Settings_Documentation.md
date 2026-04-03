# Delivery 5: FinOps Optimization & Final Defense


## 1. **Installed locus from locus.io**
Esto funcióno para un entorno Windows. Dado que hubieron problemas con dependencias y manejo de entornos en el proyecto, no se puede usar
`pip`, en lugar de ello, se optó por la siguiente ruta

### a. Instalar mediante uvx

1. [Instalar uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
2. Instalar y ejecutar locust en un entorno efímero usando por supuesto `uvx`
``` 
>> uvx locust -V 
```
### b. Pruebas

1. Entra al proyecto donde se encuentra el archivo `locust.py`

```bash
cd .\django-realworld-example-app-master\
```
2. Ejecuta el archivo `locust.py`

```
uvx locust -f locust.py
```


## 1. **Pruebas - Parametros para locus.io**

### 1. Entra a la app **locust** en http://localhost:8089/

### 2. Ingresa los parámetros de prueba

#### **a. Número de usuarios (peak concurrency)*;**

Ejemplo: `50` users, por ejemplo.

#### **b. Ramp up(users started/second)*;**

Ejemplol: `5` users/second. Llegarás al pico en 10 segundos.

#### **c. Runtime(opcional);**

Ejemplo: 2 minutos (`120s`)


Verás luego en su dashboard cómo se estresa la App con los usuarios de prueba con los parámetros correpondientes.