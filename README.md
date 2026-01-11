# 🇲🇽 Sistema de Recuperación de IVA - Demo Interactivo

[![SAT](https://img.shields.io/badge/SAT-México-green)](https://www.sat.gob.mx/)
[![CFDI](https://img.shields.io/badge/CFDI-4.0-blue)](https://www.sat.gob.mx/consultas/35025/formato-de-factura-electronica-(anexo-20))
[![Python](https://img.shields.io/badge/Python-3.8+-yellow)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

Plataforma de demostración interactiva para el proceso completo de **descarga, procesamiento y cálculo de impuestos** desde el SAT México.

🔗 **Demo en vivo:** [https://srexcel.github.io/tax/](https://srexcel.github.io/tax/)

---

## 📋 Descripción

Este proyecto documenta de forma interactiva el flujo completo para la recuperación de IVA en México:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│     🔐      │    │     📥      │    │     📊      │    │     💰      │
│ Autenticación│───▶│  Descarga   │───▶│ Aplanamiento│───▶│ Cálculo IVA │
│   (FIEL)    │    │  (SAT API)  │    │  (XMLs→CSV) │    │  (PUE/PPD)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 🚀 Flujo del Proceso

### 1️⃣ Autenticación con e.Firma (FIEL)

La **Firma Electrónica Avanzada** permite autenticarse con el SAT:

| Componente | Descripción |
|------------|-------------|
| `.cer` | Certificado público del contribuyente |
| `.key` | Llave privada cifrada |
| Contraseña | Para descifrar la llave privada |
| **Token** | Resultado: acceso autorizado al SAT |

```python
from cfdiclient import Fiel, Autenticacion

# Cargar FIEL
fiel = Fiel(cer_data, key_data, password)

# Obtener token
auth = Autenticacion(fiel)
token = auth.obtener_token()
```

### 2️⃣ Descarga Masiva de CFDIs

El SAT ofrece un servicio web para descarga masiva:

| Estado | Código | Descripción | Acción |
|--------|--------|-------------|--------|
| 📤 Aceptada | `1` | Solicitud en cola | Esperar |
| ⏳ En proceso | `2` | SAT generando archivos | Esperar |
| ✅ Lista | `3` | Paquetes disponibles | Descargar |
| ❌ Error | `4` | Falló la solicitud | Reintentar |
| 🚫 Rechazada | `5` | SAT rechazó | Verificar parámetros |

**Límites del SAT:**
- Metadata: Máximo 1,000,000 registros
- CFDI: Máximo 200,000 XMLs
- Caducidad: 72 horas
- Recomendación: Dividir en períodos de 7 días

### 3️⃣ Aplanamiento de XMLs

Los CFDIs son XMLs jerárquicos que se convierten a tablas CSV planas:

```
output/
├── _comprobante.csv        # Datos generales del CFDI
├── _concepto.csv           # Artículos/servicios facturados
├── _concepto_traslado.csv  # IVA por concepto
├── _concepto_retencion.csv # Retenciones por concepto
├── _pagos_pago.csv         # Complemento de pagos (PPD)
├── _pagos_docto.csv        # Documentos relacionados
├── _pagos_traslado_dr.csv  # IVA en pagos
└── _ledger.csv             # Registro universal
```

### 4️⃣ Cálculo de IVA

#### PUE vs PPD

| Método | Nombre | Cuándo se acredita | Complemento |
|--------|--------|-------------------|-------------|
| **PUE** | Pago en Una Exhibición | Al emitir/recibir factura | No requiere |
| **PPD** | Pago en Parcialidades/Diferido | Al pagar/cobrar | Requiere REP |

#### Fórmulas

```python
# IVA Trasladado (Ventas)
IVA_trasladado = IVA_PUE_emitidos + IVA_PPD_cobrados

# IVA Acreditable (Compras)  
IVA_acreditable = IVA_PUE_recibidos + IVA_PPD_pagados

# Saldo
Saldo = IVA_trasladado - IVA_acreditable

# Si Saldo < 0 → SALDO A FAVOR (solicitar devolución)
# Si Saldo > 0 → IVA A PAGAR
```

---

## 📁 Estructura del Proyecto

```
tax/
├── index.html          # Demo interactivo principal
├── README.md           # Esta documentación
│
├── core/
│   ├── sat_extractor.py    # Descarga masiva SAT
│   └── settings.py         # Configuración
│
├── aplanador/
│   └── cfdi_m033_logic.cpp # Aplanamiento de XMLs
│
└── calculo/
    ├── calc_acreditable_pue.py
    ├── calc_acreditable_ppd.py
    ├── calc_trasladado_pue.py
    ├── calc_trasladado_ppd.py
    └── fusion_final.py
```

---

## ⚙️ Instalación

### Requisitos

```bash
# Python 3.8+
pip install cfdiclient lxml cryptography requests
```

### Uso Básico

```python
from core.sat_extractor import SATExtractor

# Inicializar
extractor = SATExtractor()

# Agregar FIEL
extractor.fn_add_fiel_entry(
    "RFC1234567890",
    "/path/to/certificado.cer",
    "/path/to/llave.key"
)

# Seleccionar y autenticar
extractor.fn_select_fiel_by_rfc("RFC1234567890", "mi_password")
extractor.fn_authenticate()

# Iniciar descarga
from datetime import datetime
extractor.fn_start_bulk_download(
    param_start=datetime(2025, 1, 1),
    param_end=datetime(2025, 1, 31),
    param_download_type="CFDI",  # o "Metadata"
    param_cfdi_type="RECEIVED"   # o "ISSUED"
)
```

---

## 📊 Tipos de CFDI

| Tipo | Código | Descripción | Uso en IVA |
|------|--------|-------------|------------|
| **Ingreso** | `I` | Ventas, servicios | IVA Trasladado |
| **Egreso** | `E` | Notas de crédito | Ajuste de IVA |
| **Pago** | `P` | Complemento de pago | IVA PPD |
| **Traslado** | `T` | Movimiento de mercancía | No aplica IVA |
| **Nómina** | `N` | Recibos de nómina | ISR/IMSS |

---

## ⏰ Plazos de Recuperación

Según el **artículo 146 del CFF**, el derecho a solicitar devolución de IVA prescribe en **5 años**:

```
IVA a favor de:     Febrero 2021
Declaración vence:  17 de Marzo 2021
Prescripción:       17 de Marzo 2026
```

---

## 🔗 Recursos

- [SAT - Descarga Masiva](https://www.sat.gob.mx/aplicacion/91655/consulta-y-descarga-masiva-de-xml)
- [Documentación CFDI 4.0](https://www.sat.gob.mx/consultas/35025/formato-de-factura-electronica-(anexo-20))
- [cfdiclient - GitHub](https://github.com/luisiturrios1/python-cfdiclient)
- [Código Fiscal de la Federación](https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf)

---

## 📜 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

## 👤 Autor

**Cesar** - Especialista en Cumplimiento Fiscal y Desarrollo  
Consultoría en servicios fiscales para empresas internacionales, maquiladoras y operaciones de manufactura.

---

<p align="center">
  <strong>🇲🇽 Hecho en México</strong><br>
  <sub>Sistema de Recuperación de IVA © 2025</sub>
</p>
