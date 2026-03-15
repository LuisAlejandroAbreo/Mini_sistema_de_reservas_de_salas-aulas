# Analisis del proyecto: Resumen de los problemas actuales y las nececidades por cubrir

## Problema Actual: 

### *Ausencia de coordinacíon en el manejo de los salones.*

**Genera**:
 1. Conflictos de uso de los salones
 2. Solapamientos de horarios.
 3. Dificultades para planificar actividades

---

## Necesidades por Cubrir:

1. Poder saber cuales salones hay activos para uso.
2. Poder saber las fechas y horarios en los que el salon se puede usar
3. poder visualizar el horario del salon en una fecha especifica donde aparezca los tiempos reservados y disponibles.

## Preguntas Guia

- *¿Qué problema tiene la institución?*

    Ausencia de coordinacíon en el manejo de los salones

- *¿Qué objetivo debe cumplir el sistema?*

    El objetivo del sistema es permitir gestionar de forma centralizada y clara las reservas de salas y aulas, favoreciendo que la información sobre las reservas sea clara y accesible, que no haya solapamiento de horarios y facilitando la planificacion de actividades.

- *¿Quién usa el sistema?*

    Estudiantes, docentes, personal administrativo

- *¿Qué cosas necesita poder hacer el usuario?*
    
    1. Consultar qué espacios existen y, para un día o semana concreta, ver qué reservas hay asociadas a cada sala y que espacios libre hay. 
    2. Ver los detalles de una reserva especifica.
    3. Registrar una nueva reserva indicando al menos: 
        - La sala que se desea usar
        - La fecha de uso
        - El horario de inicio y de fin
        - Forma de identificar quién hace la reserva o para quién se hace (un nombre, un grupo o un curso).
        - Proposito de la reserva.
    4. Cancelar reservas.
    5. Modificar algunos datos de una reserva (como horario o sala) 

## Restricciones
- El sistema debe estar focalizado en la gestión básica de reservas, no en la administración completa de la institución
- Asumir que el sistema es usado por una sola persona a la vez o que no requiere autenticación. 
- No implementar login ni gestión de usuarios.


---