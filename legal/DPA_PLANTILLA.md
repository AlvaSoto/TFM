# Acuerdo de Encargo de Tratamiento (DPA) — Plantilla

> ⚠️ **PLANTILLA, no asesoramiento legal.** Solo es necesaria cuando se tratan
> **datos personales**. Regla práctica por segmento:
>
> | Escenario | ¿Datos personales? | ¿DPA? |
> |---|---|---|
> | Contador **general** de hotel/balneario | No (dato de la empresa) | No — basta confidencialidad en el contrato |
> | Contador de **sector/DMA** municipal | No (agregado de red) | No |
> | Contadores **domésticos** individuales (gestora, hogares) | **Sí** — el consumo revela ocupación y hábitos (considerando RGPD) | **Sí** + ver notas RGPD |

---

## Anexo III — Encargo de tratamiento (art. 28 RGPD)

**Responsable**: [Cliente/gestora] · **Encargado**: [Tu razón social]

### 1. Objeto y duración
Tratamiento de datos de consumo de agua de contadores individuales para la
detección de anomalías y comunicación de alertas, durante la vigencia del
contrato de servicio.

### 2. Naturaleza y finalidad
- Datos tratados: identificador de contador/póliza, series temporales de
  consumo, [dirección/zona], [email del abonado si hay app ciudadana].
- **No se tratan** categorías especiales de datos.
- Finalidad exclusiva: detección de fugas/anomalías, estimación económica,
  informes al Responsable [y avisos al abonado, si se pacta].

### 3. Obligaciones del Encargado
1. Tratar los datos solo según instrucciones documentadas del Responsable.
2. Confidencialidad del personal con acceso.
3. Medidas de seguridad (art. 32): cifrado en tránsito (TLS), control de
   acceso por cliente (multi-tenant con autenticación), copias de seguridad
   diarias, registro de accesos, seudonimización de identificadores cuando
   sea posible.
4. No subcontratar sin autorización escrita. Subencargados actuales:
   [hosting: ___, ubicación UE; email: ___].
5. Asistir al Responsable ante ejercicios de derechos (acceso, supresión...)
   y ante violaciones de seguridad (notificación al Responsable sin dilación
   y en máximo **48 h** desde su conocimiento).
6. A fin de contrato: devolución de datos en formato reutilizable (CSV) y
   supresión certificada, salvo obligación legal de conservación.
7. Poner a disposición la información necesaria para auditorías.

### 4. Ubicación del tratamiento
Los datos se alojan en [proveedor y región — usar región UE]. Sin
transferencias fuera del EEE [o: con las garantías del art. 46 — cláusulas
tipo con [proveedor]].

### 5. Opción recomendada para gestoras
Despliegue **en la infraestructura del Responsable** (on-premise / su nube):
el Encargado accede solo para mantenimiento. Simplifica drásticamente el
análisis de riesgos y suele desbloquear la firma.
