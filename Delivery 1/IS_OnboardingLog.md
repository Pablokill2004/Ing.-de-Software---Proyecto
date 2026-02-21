# Onboarding Log - Django RealWorld

## Entorno
---
- OS: Kali Linux(VM)

##  Walkthrough
---
### **1. Clonar el repositorio**

#### a. Friction Point

Al intentar clonar el repo usando GitBash en nuestra máquina principal, nos encontramos con un mensaje.
```
The authenticity of host 'github.com (...)' can't be established.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Investigando un poco esto pasa porque nos conectamos a github desde SSH.

#### b. Root cause

El repositorio **asume** que el desarrollador:

- Tiene SSH configurado
- Tiene una clave SSH cargada en GitHub
- Sabe cómo responder a este prompt

Pero no es asi.

Seguidamente escribimos "yes" pero obtuvimos lo siguiente:

```
Warning: Permanently added 'github.com' (ED25519) to the list of known hosts.
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
Please make sure you have the correct access rights
and the repository exists.
```


El repositorio asume que los desarrolladores ya tienen claves SSH configuradas y asociadas a cuentas de GitHub. No hay documentación de incorporación que explique este requisito.


#### c. Workaround

Evitamos el SSH, y usamos HTTPS para clonar el repositorio.

```
>> git clone https://github.com/gothinkster/productionready-django-api.git
```

#### d. Impact

Bloquea el primer paso de onboarding.

### **3. Install `pyenv`.**

####a. Friction Point

No se especifica para qué sirve este dependencia. Pero investigando un poco:
`pyenv` es un gestor de versiones de Python. Sirve para instalar y cambiar entre múltiples versiones de Python fácilmente por proyecto.

En Windows, `pyenv` no se soporta oficialmente.

#### b. Workaround

Se usó una VM para trabajar en el entorno Linux, y así darnos una mayor facilidad en la adaptacion de estas dependencias.

#### c. Impact

Los usuario de windows podrían quedar bloqueados o confundidos

### **4. Install `pyenv-virtualenv.`**

Instalacion completada, siguiendo con las especificaciones del repositorio linkeado en el archivo `README.md`

### **5. Install Python 3.5.2 `pyenv install 3.5.2`**

#### a. Friction Point

El archivo README requiere Python 3.5.2. La instalación falla en distribuciones modernas de Linux que usan pyenv; incompatibilidad por versión obsoleta.

Por ahora se intentó utilizar una versión más adelantada(3.8.0) pero surge otro problema:

` ERROR: The Python ssl extension was not compiled. BUILD FAILED`

Sin `ssl`, Python queda inutilizable para:
- pip
- https
- instalar dependencias
- Django

Prácticamente Python no sirve para el proyecto.

Incluso después de seleccionar una versión más nueva de Python, la configuración del entorno falla debido a dependencias del sistema no documentadas.

#### b. Workaround

Se instalaron las librerías necesarias y descritas en el Log cuando intentamos instalar la versioin de Python:

- OpenSSL
- bzip2
- readline
- zlib, etc.

A continuación el script

`sudo apt update`

`sudo apt install -y `

`make build-essential libssl-dev zlib1g-dev `

`libbz2-dev libreadline-dev libsqlite3-dev `

`wget curl llvm libncursesw5-dev xz-utils `

`tk-dev libxml2-dev libxmlsec1-dev libffi-dev`

Luego instalamos una version de python un poco más reciente `pyenv install 3.5.2`

#### c. Impact

Aumenta el tiempo de settup y probabilidad de errores.

### **6. Create a new virtualenv called `productionready`: `pyenv virtualenv 3.5.2 productionready.`**

#### a. Observations

Se debe especificar mejor si no hay problema en donde ejecutar cada script

#### b. Workaround

Se ejcuto el script en `/home/kali` aunque investigando un poco más, lo que hace pyenv es que crea entornos en `~/.pyenv/versions/` por lo que no afecta en qué ubicacion ejecutar este script.

### **7. Falta de especificaciones en la instalacion de depencencias**

####a. Friction Point

El `README.md` no menciona que se debe instalar las Python dependencies

`pip install -r requirements.txt`

#### b. Impact

Los nuevos devs deben adivinar cuales son las dependencias a instalar y cómo.

