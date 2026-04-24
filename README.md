# 💧 Smart Water Monitor

<div align="center">

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.18-FF6F00?logo=tensorflow&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Plataforma Inteligente de Detección de Fugas Hídricas mediante Deep Learning**

[Ver Demo](#) · [Documentación](#) · [Reportar Bug](https://github.com/AlvaSoto/TFM/issues)

</div>

---

## 🎯 Descripción del Proyecto

Smart Water Monitor es una plataforma de monitorización en tiempo real que utiliza técnicas avanzadas de **Deep Learning** para detectar anomalías en el consumo de agua, prevenir pérdidas y optimizar el uso de recursos hídricos.

### 🏆 Trabajo Final de Máster
- **Institución:** Universidad Europea
- **Programa:** Máster en Inteligencia Artificial
- **Año:** 2026
- **Autor:** Álvaro Soto Álvarez

---

## ✨ Características Principales

### 🤖 IA Predictiva
- **LSTM Autoencoder** entrenado con 2.7M puntos de datos
- **ROC-AUC: 93.7%** - Excelente capacidad de discriminación
- **Recall: 71%** - Detecta 7 de cada 10 fugas reales
- Análisis mediante MSE (Mean Squared Error)
- Umbral adaptativo (Percentil 96)

### 📊 Dashboard Interactivo
- Visualización de consumo en tiempo real
- Gráficas interactivas con Recharts
- Comparativas con la comunidad
- Alertas visuales de fugas

### 🧠 Asistente IA (GPT-4o)
- Recomendaciones personalizadas
- Análisis de impacto económico
- Consejos de optimización
- Diagnósticos automáticos

### 📈 Análisis Financiero
- Estimación de factura mensual
- Cálculo de costes por región
- Historial de consumo
- Análisis de ahorro potencial

---

## 🚀 Tecnologías Utilizadas

### Backend
```
Python 3.10
├── FastAPI          # API REST de alto rendimiento
├── TensorFlow 2.18  # Deep Learning Framework
├── Keras 3.12       # API de alto nivel para redes neuronales
├── Pandas & NumPy   # Análisis de datos
├── Scikit-learn     # Preprocesamiento y métricas
└── OpenAI API       # Integración con GPT-4o
```

### Frontend
```
React 18
├── Vite             # Build tool ultrarrápido
├── Tailwind CSS     # Framework de estilos
├── Recharts         # Visualización de datos
├── Framer Motion    # Animaciones fluidas
└── Lucide Icons     # Iconos modernos
```

### Machine Learning

**Arquitectura: LSTM Autoencoder para Detección de Anomalías**

```
Input: Secuencia de 96 timesteps (24h con intervalos de 15 min) × 14 features

Encoder (Compresión):
├── LSTM Layer 1: 256 unidades → Aprende patrones complejos
├── LSTM Layer 2: 128 unidades → Reduce dimensionalidad
└── LSTM Layer 3: 64 unidades  → Representación latente compacta

Bottleneck (Latent Space):
└── 64 dimensiones → Codificación del patrón normal

Decoder (Reconstrucción):
├── LSTM Layer 4: 64 unidades  → Expande desde latent space
├── LSTM Layer 5: 128 unidades → Reconstruye secuencia
├── LSTM Layer 6: 256 unidades → Detalle fino
└── Dense Layer: 14 outputs    → Reconstrucción de features

Output: Secuencia reconstruida (mismo tamaño que input)

Pérdida: MSE (Mean Squared Error)
└── MSE bajo  → Patrón normal (reconstrucción exitosa)
└── MSE alto  → Anomalía detectada (reconstrucción fallida)

Training:
├── Datos: 2.7M registros (solo consumo normal)
├── Épocas: 150 con Early Stopping
├── Batch Size: 256
└── Validación: 15% del dataset
```

**¿Cómo detecta fugas?**
1. El modelo aprende a reconstruir SOLO consumo normal
2. Cuando ve una fuga, intenta reconstruirla como consumo normal
3. Falla → MSE aumenta significativamente
4. Si MSE > umbral (0.52) → ALERTA DE FUGA

---

## 📊 Dataset & Métricas

### Simulación de Datos
- **160 hogares** con perfiles diversos
- **180 días** de monitorización continua
- **Intervalos de 15 minutos** (96 mediciones/día)
- **2,764,800 puntos de datos** en total

### Tipos de Hogares Simulados
- Apartamento (persona sola)
- Apartamento (familia 4 personas)
- Casa con jardín (familia 4 personas)

### Métricas de Rendimiento
| Métrica | Valor | Descripción |
|---------|-------|-------------|
| ROC-AUC | 93.7% | Capacidad de discriminación |
| Recall | 71% | Detecta 7/10 fugas reales |
| Precision | 48% | Balance FP/TP optimizado |
| Umbral | MSE > 0.52 | Percentil 96 |
| Dataset | 2.7M registros | 150 épocas entrenamiento |
| Latencia | < 1s | Detección en tiempo real |

---

## 🛠️ Instalación

### Requisitos Previos
- Python 3.10+
- Node.js 22.12.0+
- Anaconda/Miniconda (recomendado)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/AlvaSoto/TFM.git
cd TFM
```

### 2. Configurar Backend

#### Opción A: Con Anaconda (Recomendado)
```bash
conda create -n TFM python=3.10
conda activate TFM
cd backend
pip install -r requirements.txt
```

#### Opción B: Con venv
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar Frontend
```bash
cd frontend
npm install
```

---

## 🚀 Uso

### Iniciar Backend
```bash
# Con Makefile
make run-backend

# O manualmente
cd backend
uvicorn app.api.router:app --reload
```

El backend estará disponible en: `http://localhost:8000`

### Iniciar Frontend
```bash
# Con Makefile
make run-frontend

# O manualmente
cd frontend
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

### Comandos Útiles
```bash
make install-backend    # Instalar dependencias backend
make install-frontend   # Instalar dependencias frontend
make clean-all         # Limpiar archivos temporales
```

---

## 📁 Estructura del Proyecto

```
TFM/
├── backend/
│   ├── app/
│   │   ├── api/              # Endpoints FastAPI
│   │   ├── core/             # Configuración
│   │   ├── models/           # Modelos de datos
│   │   ├── services/         # Lógica de negocio
│   │   ├── simulators/       # Simulador de datos
│   │   └── ml/               # Notebooks ML
│   ├── data/                 # Datasets
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   ├── services/         # API client
│   │   └── App.jsx
│   └── package.json
│
└── Makefile                  # Automatización
```

---

## 🔬 Arquitectura del Sistema

### Enfoque: Detección de Anomalías mediante Autoencoder

El sistema utiliza un **LSTM Autoencoder** que aprende a reconstruir patrones de consumo normales. Cuando encuentra una fuga, el error de reconstrucción (MSE) aumenta significativamente.

#### 📐 Proceso de Detección

1. **Entrenamiento**: El modelo aprende únicamente de datos normales (sin fugas)
2. **Reconstrucción**: Para nuevos datos, intenta reconstruir el patrón
3. **Error MSE**: Calcula la diferencia entre entrada y reconstrucción
4. **Umbral**: Si MSE > 0.52 (percentil 96) → Alerta de fuga
5. **Decisión**: Prioriza Recall sobre Precision para evitar fugas no detectadas

#### 🎯 Balance Precision vs Recall

```
Percentil 96 (Configuración Actual):
├─ Recall: 71% → Detecta 7 de cada 10 fugas
├─ Precision: 48% → 1 de cada 2 alertas es real fuga
└─ Filosofía: Mejor un falso positivo que una fuga sin detectar

Percentil 99 (Más conservador):
├─ Recall: 35% → Solo detecta las fugas más evidentes
├─ Precision: 95% → Muy pocas falsas alarmas
└─ Riesgo: Pierde muchas fugas sutiles
```

#### 🧠 ¿Por qué funciona?

- **Clase desbalanceada**: 133,768 registros normales vs 3,725 con fugas
- **Aprendizaje no supervisado**: No necesita ejemplos de fugas para entrenar
- **ROC-AUC 93.7%**: El modelo tiene 93.7% de probabilidad de asignar mayor error a una fuga que a consumo normal
- **MSE como proxy**: Un error alto de reconstrucción indica patrón anómalo

```
┌─────────────────┐
│   Frontend      │
│   React + Vite  │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   API Gateway   │
│    FastAPI      │
└────────┬────────┘
         │
    ┌────┴─────────────────┐
    │                      │
    ▼                      ▼
┌─────────┐          ┌──────────┐
│  Data   │          │ ML Model │
│ Service │          │  LSTM    │
└─────────┘          └──────────┘
    │                      │
    ▼                      ▼
┌──────────────────────────────┐
│      Detector Service         │
│  - Feature Engineering        │
│  - Anomaly Detection          │
│  - Threshold Analysis         │
└──────────────────────────────┘
```

---

## 🧪 Generar Nuevo Dataset

Para crear un nuevo dataset simulado:

```bash
cd backend
python -m app.simulators.water_compsumption_simulator
```

Esto generará:
- `mixed_population_dataset_160_households_more_leaks.csv`
- `detailed_events_log_160_households.csv`

---

## 📸 Capturas de Pantalla

### Landing Page
![Landing Page](screenshots/landing.png)

### Dashboard Principal
![Dashboard](screenshots/dashboard.png)

### Detección de Fugas
![Leak Detection](screenshots/leak-detection.png)

---

## 🎯 Roadmap

- [x] Desarrollo del modelo LSTM Autoencoder
- [x] API REST con FastAPI
- [x] Dashboard interactivo con React
- [x] Integración con GPT-4o
- [x] Sistema de alertas en tiempo real
- [ ] Aplicación móvil (iOS/Android)
- [ ] Notificaciones push
- [ ] Integración con sensores IoT
- [ ] Despliegue en producción (AWS/GCP)

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más información.

---

## 👤 Autor

**Álvaro Soto Álvarez**

- LinkedIn: [linkedin.com/in/alvarosoto](https://linkedin.com/in/alvarosoto)
- GitHub: [@AlvaSoto](https://github.com/AlvaSoto)
- Email: contact@example.com

---

## 🙏 Agradecimientos

- Universidad Europea - Programa de Máster en IA
- OpenAI - Por la API de GPT-4o
- Comunidad de TensorFlow y React
- Todos los contribuidores del proyecto

---

<div align="center">

**⭐ Si te ha gustado este proyecto, considera darle una estrella ⭐**

Desarrollado con ❤️ por Álvaro Soto Álvarez © 2026

</div>
