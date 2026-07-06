# RGPD — notas operativas y guion de DPIA

> ⚠️ Notas de trabajo, no asesoramiento legal. Úsalas para llegar preparado a
> la conversación con el DPO del cliente y con tu abogado.

## Mapa de riesgo por segmento

**Hotel / balneario (contador general)** — Sin datos personales: el consumo
agregado de un edificio empresarial no identifica personas. Basta la cláusula
de confidencialidad del contrato. *Es la razón por la que el hotel es el mejor
segmento de entrada.*

**Pueblo / sector DMA** — Sin datos personales mientras el punto agregue ≥
[~20] viviendas. Cuidado con sectores muy pequeños (una calle de 3 casas
empieza a ser identificable). Regla interna: no monitorizar agregados de
menos de 10 viviendas sin tratarlos como personales.

**Contadores domésticos individuales (gestora)** — Datos personales, y
sensibles en la práctica: la serie de consumo revela ocupación de la
vivienda, horarios y hábitos. Aquí aplica el paquete completo: DPA + DPIA +
minimización. La base jurídica habitual es el **interés legítimo de la
gestora** (detección de fugas, ya presta el servicio de agua) o la ejecución
del contrato de suministro; el aviso al abonado conviene articularlo como
mejora del servicio con información clara.

## Medidas de minimización que YA implementa el producto (contarlas así)

- Multi-tenant con autenticación: cada cliente ve exclusivamente sus datos.
- Seudonimización natural: el sistema opera con IDs de contador, no nombres.
- El dato nunca sale del ámbito del servicio; opción de despliegue en la
  infraestructura del cliente.
- Ingesta autenticada por clave por cliente; TLS en tránsito.
- Retención definida: [24] meses de series (config del cliente) + backups 14 días.
- El LLM (informes en lenguaje natural) recibe solo agregados/IDs de contador,
  nunca identidad del abonado. [Si el cliente lo exige: desactivable.]

## Guion de DPIA (evaluación de impacto — solo despliegues domésticos)

1. **Descripción del tratamiento**: series de consumo por póliza cada [15-60]
   min; finalidad: detección de fugas y aviso; sistemas: [infra]; flujo:
   contador → pasarela → API → detección → alerta.
2. **Necesidad y proporcionalidad**: ¿se puede lograr con menos dato? →
   justificar la resolución elegida (la detección nocturna exige al menos
   lecturas horarias); retención mínima necesaria para línea base estacional.
3. **Riesgos**: inferencia de ocupación (robo), perfilado de hábitos, acceso
   indebido, re-identificación. Probabilidad × impacto por cada uno.
4. **Mitigaciones**: las de arriba + acceso del personal del Proveedor bajo
   registro + alertas solo con dato mínimo (contador, fechas, litros).
5. **Conclusión y firma** del responsable + consulta al DPO del cliente.

## Checklist antes de firmar con una gestora

- [ ] DPA firmado (plantilla en `legal/DPA_PLANTILLA.md`)
- [ ] DPIA hecha con su DPO (guion arriba)
- [ ] Registro de actividades de tratamiento actualizado (el tuyo como encargado)
- [ ] Hosting en región UE confirmado por escrito
- [ ] Procedimiento de brechas pactado (48 h al responsable)
- [ ] Cláusula de datos agregados/anonimizados para mejora de modelos
