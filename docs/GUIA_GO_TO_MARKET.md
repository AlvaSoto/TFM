# Guía Go-To-Market — paso a paso

Los 9 puntos que separan el proyecto del mercado, con el "cómo" concreto de
cada uno. Estado a 2026-07: los puntos 4, 5, 7, 8 y 9 están **implementados
en este repo**; los puntos 1, 2, 3 y 6 son acciones tuyas fuera del código.

---

## 1. La historia de hardware 🔧 *(acción tuya — esta semana)*

**Objetivo**: poder decir en una reunión "instalamos ESTE dispositivo, tarda
una mañana" y que sea verdad porque lo has hecho tú.

**Paso a paso:**
1. **Compra un kit de pruebas** (~150-250 € total):
   - *Opción A (sin tocar la tubería)*: contador con emisor de pulsos tipo
     reed (p. ej. clase B DN15-DN25 con salida de pulsos, 1 pulso = 1-10 L,
     ~40-70 €) + contador de pulsos LoRaWAN o NB-IoT (Dragino SW3L o
     equivalente, ~60-100 €) + gateway LoRaWAN si no hay cobertura (Dragino
     LPS8, ~100 €) — busca en tiendas IoT españolas o Amazon industrial.
   - *Opción B (si el cliente ya tiene telelectura)*: no hay hardware — pide
     el export CSV/API de su plataforma AMI y usa `/api/v1/ingest/csv`.
2. **Móntalo en tu propia casa**: en la entrada del contador o en la toma de
   un aseo. Configura el emisor → gateway → un webhook/script que haga POST
   a tu `/api/v1/ingest/readings` (formato en el README).
3. **Déjalo 3-4 semanas**: tendrás tu primer contador real permanente, tu
   demo con datos reales y todo el aprendizaje de instalación.
4. **Busca el partner instalador**: un fontanero o integrador local que haga
   la instalación en casa del cliente por 100-200 €/punto. Preséntale el
   negocio: tú le traes trabajos recurrentes.

**Hecho cuando**: tu contador manda lecturas cada hora a tu API y sabes
instalar el kit en <2 horas.

## 2. Poder cobrar 💶 *(acción tuya — cuando haya un "sí" a la vista)*

1. **Alta de autónomo** (basta para el primer piloto): alta censal (modelo
   036/037, epígrafe IAE 843.9 u 899) + alta RETA. Se hace online en un día.
   Si tienes nómina, la pluriactividad reduce la cuota. La SL espera al
   segundo cliente o a facturar >40-50k €/año.
2. **Seguro de responsabilidad civil profesional** (~150-300 €/año): te lo
   pedirán antes de dejarte tocar una instalación.
3. **Precio decidido antes de la primera reunión** (no lo improvises):
   - Piloto hotel/balneario: **1.500-3.000 € + IVA** (hardware + instalación
     + 6 semanas de servicio + informe final). Nunca gratis.
   - Suscripción posterior: **100-300 €/mes** por instalación hotelera;
     municipios por punto de medida (50-150 €/punto/mes según volumen);
     gestoras: licencia por contador/mes (0,10-0,30 €) — negociación aparte.
   - Ancla el precio al valor: una sola fuga de cisterna son >50.000 L/año.

## 3. La propuesta de piloto tipo 📄 *(hecha — personalizar por cliente)*

Usa `docs/PROPUESTA_PILOTO_PLANTILLA.md`: rellena los corchetes, exporta a
PDF y llévala a la segunda reunión (la primera es para escuchar). Las métricas
de éxito del Anexo son la clave: pactadas por escrito, el piloto se defiende
solo al acabar.

## 4. Scoring automático nocturno ⚙️ *(implementado)*

`python -m app.jobs.nightly` re-analiza cada contador real con sus lecturas
acumuladas y dispara las alertas de transición a CONFIRMADA.

```cron
15 6 * * *  cd /ruta/backend && /ruta/python -m app.jobs.nightly >> /var/log/swm_nightly.log 2>&1
30 5 * * *  /ruta/backend/scripts/backup.sh /ruta/backups
0  8 * * 1  cd /ruta/backend && /ruta/python -m app.jobs.weekly_report >> /var/log/swm_weekly.log 2>&1
```

## 5. Informe semanal automático 📬 *(implementado)*

`python -m app.jobs.weekly_report` — por tenant, con consumo de la semana,
alertas y pérdida estimada en €. Se envía al `report_email` del tenant si hay
SMTP configurado; si no, lo imprime (revísalo así antes de activar el envío).

## 6. Identidad separada del TFM 🏷 *(acción tuya — antes de enseñar el repo)*

1. **Nombre**: "Smart Water Monitor" es genérico (no registrable, no
   posicionable). Haz una lista de 10 candidatos, comprueba dominio (.es/.com
   libres), marca (búsqueda en OEPM: sede.oepm.gob.es) y que no exista una
   empresa igual (registro mercantil). Registrar la marca española: ~150 €,
   online, sin abogado.
2. **Dominio + email** (~15 €/año): landing en el dominio y email
   hola@tudominio — cambia el mailto de `landing/index.html` y el contacto
   del README.
3. **Repo**: renómbralo (GitHub → Settings → Rename, las URLs antiguas
   redirigen) y considera hacerlo privado si vas a enseñar el código solo
   bajo NDA. El README ya está reescrito como producto.

## 7. Multi-tenant + auth ✅ *(implementado)*

- Crear un cliente: `python -m app.core.tenants create --id hotel_costa
  --name "Hotel Costa" --email ops@hotelcosta.com` → devuelve contraseña de
  consola y API key de ingesta (guárdalas: no se vuelven a mostrar).
- Cada tenant ve SOLO sus contadores; branding (nombre+color) en la consola;
  sesiones de 12 h con token firmado. **Sin tenants configurados, la app
  sigue en modo abierto** para desarrollo/demos.

## 8. Operación mínima ✅ *(implementado)*

- **Backup**: `scripts/backup.sh` (SQLite consistente + estado + tenants,
  rotación 14 días). Prográmalo ANTES del primer dato real de cliente.
- **Uptime**: endpoint `/health` sin auth. Crea un monitor gratuito en
  UptimeRobot (uptimerobot.com → Add Monitor → HTTP(s) → tu-servidor/health,
  cada 5 min, alerta a tu email). 5 minutos de configurar.
- **Recalibración**: procedimiento completo en `docs/PLAYBOOK_RECALIBRACION.md`.

## 9. Papeles ✅ *(plantillas hechas — revisar con abogado antes de firmar)*

- `legal/TERMINOS_SERVICIO_PLANTILLA.md` — contrato de piloto con limitación
  de responsabilidad (la cláusula 6 es la importante: el servicio APOYA la
  detección, no garantiza detectar toda fuga).
- `legal/DPA_PLANTILLA.md` — solo para despliegues con datos personales
  (hogares); hoteles y DMA no lo necesitan.
- `legal/RGPD_NOTAS.md` — mapa de riesgo por segmento y guion de DPIA para
  llegar preparado a la conversación con el DPO de una gestora.

---

## Orden de ejecución sugerido

**Semana 1**: kit de hardware pedido + montado en tu casa · candidaturas
GoHub/Cajamar enviadas · naming + dominio.
**Semanas 2-4**: conversaciones (guion: escuchar cuánto les cuesta hoy no
saber; la demo al final, no al principio) · configurar UptimeRobot + cron en
tu servidor de demo.
**Cuando llegue el "sí"**: alta autónomo + seguro RC → personalizar propuesta
→ firmar → crear tenant → instalar → el sistema hace el resto.
