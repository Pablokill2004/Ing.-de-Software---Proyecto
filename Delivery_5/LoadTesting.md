# Delivery 5: FinOps Optimization & Final Defense

>*"Benchmark: Provide a "Before vs. After" comparison of performance and theoretical cost reduction."*

## 1. **Installed locus from locus.io**
Esto funcióno para un entorno Windows. Dado que hubieron problemas con dependencias y manejo de entornos en el proyecto, no se puede usar
`pip`, en lugar de ello, se optó por la siguiente ruta

### a. Instalar mediante uvx

1. [Instalar uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
2. Instalar y ejecutar locust en un entorno efímero usando por supuesto `uvx`
``` 
>> uvx locust -V 
```
