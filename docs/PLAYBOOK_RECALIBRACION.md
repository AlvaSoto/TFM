# Playbook de recalibración con datos reales

Procedimiento operativo para reentrenar y desplegar los modelos durante un
piloto, sin romper nada y pudiendo demostrar siempre qué corre y por qué.

## Principios (no negociables)

1. **Nunca se despliega un modelo sin evaluarlo antes contra el que está en producción.**
2. **El umbral viaja siempre con el modelo** (`threshold.json`) — jamás se edita a mano.
3. **Todo despliegue es reversible**: los artefactos anteriores se archivan con fecha.
4. **Los periodos con fuga confirmada se excluyen del entrenamiento** (el modelo
   aprende "lo normal"; una fuga en el train contaminaría la línea base).

## Cuándo recalibrar

| Situación | Acción |
|---|---|
| Nuevo contador real conectado | Nada: MNF-trending funciona desde la noche 8; el forecaster necesita ≥28 días de historia propia |
| Contador con 4+ semanas de datos | Primer entrenamiento con sus datos (añadirlo al set de train) |
| Falsa alarma confirmada por el cliente | Anotarla (fecha+contador), revisar si es patrón legítimo nuevo (p. ej. riego programado) → reentrenar incluyendo ese periodo como normal |
| Fuga real confirmada y reparada | Marcar el periodo como fuga (excluir del train) y usarlo como caso de test etiquetado — **oro**: es tu primer ground truth real |
| Cambio estructural en la instalación (reforma, nueva piscina...) | Resetear la línea base de ese contador (reentrenar solo con datos posteriores al cambio) |
| Deriva sin causa (alertas suben sin fugas) | Revisar distribución de residuos del forecaster; si el P50 queda sesgado >10%, reentrenar |

## Procedimiento de reentrenamiento (forecaster, ~5 min)

```bash
cd backend
# 1. Exportar las lecturas reales + etiquetas conocidas a CSV de entrenamiento
#    (excluyendo periodos de fuga confirmada)
# 2. Entrenar
python -m app.ml.forecaster            # artefactos → app/ml/forecaster_artifacts/
# 3. La evaluación se imprime al final: compárala con la de producción
python -m app.ml.evaluate_aggregated
```

## Procedimiento LSTM (hogares, sesión de Kaggle)

Usar `app/ml/kaggle_train_clean.ipynb` (instrucciones dentro). Al terminar:
descargar `Run_Clean_artifacts.zip` y seguir la tabla de despliegue de la
última celda del notebook.

## Validación antes de desplegar (checklist)

- [ ] Métricas del candidato ≥ métricas del modelo en producción en el MISMO
      conjunto de test (día-nivel: precision de CONFIRMADAS y recall de OR)
- [ ] Cero regresión en los casos etiquetados reales acumulados (cada fuga
      confirmada de un piloto se convierte en test permanente)
- [ ] `threshold.json` regenerado por el pipeline (no editado)
- [ ] Artefactos anteriores archivados: `backup_modelo_YYYYMMDD/`

## Despliegue

```bash
RUN=app/simulators/Azure_model_new_data/resultados/Run_Ultimate
mkdir -p $RUN/backup_modelo_$(date +%Y%m%d)
cp $RUN/checkpoints/best_model.keras $RUN/results/scaler.joblib $RUN/backup_modelo_$(date +%Y%m%d)/
# copiar los artefactos nuevos a sus rutas y reiniciar el backend
rm -f data/fleet_scores.json          # el scoring se regenera con el modelo nuevo
python -m app.services.fleet          # re-puntuar
python -m app.ml.evaluate_ensemble    # dejar constancia de las métricas desplegadas
```

La vista **Sistema** de la consola refleja el cambio (umbral, origen, métricas):
haz captura para el registro del piloto.

## Rollback

Copiar de vuelta los artefactos de `backup_modelo_YYYYMMDD/`, borrar
`fleet_scores.json`, re-puntuar. Total: 5 minutos.
