# Ferrépolis

## Propósito
El propósito de este repositorio es alojar los desarrollos realizados para la empresa Ferrepolis.
La estrucutra de las ramas y el objetivo de cada una de ellas se mencionan a continuación:

### Rama main
La rama **main** contiene los desarrollos utilizados en el ambiente productivo del grupo Ferrepolis. Esta rama no debe ser utilizada para realizar modificaciones de forma directa, en lugar de eso, se deben incluir las modificaciones que ya han sido desarrolladas y probadas en la rama **dev**.

### Rama dev
La rama **dev** contiene los desarrollos utilizados en cualquier ambiente de desarrollo del grupo Ferrepolis. El objetivo es utilizar esta rama para realizar cualquier mejora, modificación o corrección antes de migrar al ambiente productivo, es decir, a la rama **main**.

## Desarrollo
Las ramas utilizadas para modificaciones, mejoras o correciones será la de **dev**.

### Lista de motivos
A continuación, se presenta la lista de motivos para las modificaciones de desarrollos:

* [NEW] Se usará cuando se agreguen nuevos módulos o aplicaciones al código.
* [UPDATE] Se usará cuando se agreguen nuevas características al código existente.
* [FIX] Se usará cuando  el funcionamiento del módulo no es el correcto y se debe realizar una corrección.
* [DELETE] Se utilizará cuando se borran elementos como modelos, campos, métodos, vistas, etc.

### Descripción del commit
La descripción utilizada al realizar un commit -m, debe tener la siguiente estructura:

```
[<motivo> <#ticket>] <comentario>
```
Por ejemplo:
```
[UPDATE #54] Plantilla XML para nómina
[FIX #12] Error al cargar certificados SAT
```
El motivo indicado en el commit debe corresponder a uno de la Lista de motivos del apartado anterior. Si el commit se realiza derivado de un ticket establecido en la mesa de ayuda, deberá de indicarse. El comentario en el commit deberá ser breve, y procurar utilizar menos de 50 caractéres.

### Restauración de ambiente
Al momento de crear una instancia de desarrollo (local o web), es **importante considerar los siguientes elementos**:

* Quitar los certificados CFDI y habilitar el ambiente de desarrollo.
* Quitar los servidores (entrantes/salientes) de correo electrónico.

Para quitar los certificados y servidores de correo, existe un módulo llamado **development_enviroment** que nos ayudará a realizar esta operación de forma rápida. Los pasos para realizar esta acción son los siguientes:

* Instalar el módulo en el ambiete.
* Ir al apartado de Acciones Planificadas.
* Buscar la acción llamada: Habilitar Ambiente Desarrollo.
* Ejecutar manualmente dicha acción.

Se puede verificar el resultado, yendo al apartado Ajustes > Opciones Generales > Contabilidad > Contabilidad MX.
