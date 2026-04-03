
# Django-realworld-example | Discovery & Reverse Engineering

## Elección de proyecto
Decidimos dar paso al analisis de éste proyecto para analizar las faltas y friccioens que pueden existir en un proyecto donde la documentación y especificación es muy escasa y al que se le debería dar mejor integración continua(CI).

Es muy interesante ver cómo,  desde la perspectiva de un nuevo dev, la falta de documentación y especificación puede llevar a que se quede estancado - debido a las fricciones - y por consiguiente, no poder saber hacer nada o quedarse confundido.

### Onboarding Log
- Se documentaron pasos de onboarding
- Se identificaron friction points 
- Se mostraron resoluciones

[Ver Onboarding Log](IS_OnboardingLog.md)

### Context Map
- Qué bounded contexts existen
- Derivadas del análisis del código
- Cada una está asociada a módulos/archivos específicos

[Ver Context Map ](ContextMap.md)
 
### Backlog Recovery
- Derivadas del análisis del código
- Cada una está asociada a módulos/archivos del proyecto.

[Ver Backlog Recovery](Backlog_Recovery.md)


## Desiciones no triviales

### Máquina virtual/Entonro virtual en lugar de windows

El README no menciona Windows o un entorno especifico;
`pyenv` no se soporta oficialmente en Windows, por lo que puede ser un poco confuso utilizar otra alternativa diferente y aún más, sino se especifica si pueda haber diferencias.


### Instalación de dependencias manuales

Esto para la compilación de `python`, donde el README no lista dependencias, por lo que se requirió investigación adicional sobre la instalación de dependencias necesarias.

### Instalar `requirements.txt`

Sin que estuviese **explísitamente** documentado, debimos ejecutar mediante `pip install -r requirements.txt` dichas dependencias para la correcta ejecución de Django.

