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

Los CFDIs son XMLs jerárquicos que se convierten a tablas CSV planas. **Existen dos métodos** según el volumen:

#### Método Python (< 50,000 CFDIs)

```bash
# Paso 1: Extraer estructura (1a.py)
python 1a.py
# Output: TEMPZ_YYYYMMDD_HHMMSS.csv (formato largo: Or, Var, Val, UUID)

# Paso 2: Pivotear y mapear (2a.py)  
python 2a.py
# Output: TEMPZ_SUM.csv (listo para cálculo)
```

| Característica | Valor |
|----------------|-------|
| **Velocidad** | ~100-500 XMLs/seg |
| **Output** | 1 CSV unificado |
| **Uso** | Desarrollo, pruebas |
| **Ventaja** | Flexible, fácil de modificar |

#### Método C++ (> 50,000 CFDIs)

```bash
./cfdi_m038 -i /ruta/xmls -o /ruta/output
# Output: 25+ archivos CSV especializados
```

| Característica | Valor |
|----------------|-------|
| **Velocidad** | ~5,000-10,000 XMLs/seg |
| **Output** | 25+ CSVs especializados |
| **Uso** | Producción, volúmenes altos |
| **Ventaja** | Ultra rápido, multihilo |

#### Archivos CSV Generados (Método C++)

```
output/
├── CFDI Base
│   ├── _comprobante.csv        # Datos generales (UUID, Fecha, Total, MetodoPago)
│   ├── _emisor.csv             # RFC, Nombre, Régimen del emisor
│   ├── _receptor.csv           # RFC, Nombre, UsoCFDI del receptor
│   └── _cfdi_relacionados.csv  # Documentos relacionados
│
├── Conceptos
│   ├── _concepto.csv           # Artículos/servicios facturados
│   ├── _concepto_traslado.csv  # IVA por concepto ⭐
│   ├── _concepto_retencion.csv # Retenciones por concepto
│   ├── _informacion_aduanera.csv
│   ├── _cuenta_predial.csv
│   └── _parte.csv
│
├── Impuestos Comprobante
│   ├── _impuestos_traslado.csv # Totales IVA
│   └── _impuestos_retencion.csv
│
├── Complemento Pagos (PPD) ⭐
│   ├── _pagos_pago.csv         # Cada pago recibido
│   ├── _pagos_docto.csv        # Documentos pagados
│   ├── _pagos_totales.csv      # Resumen
│   ├── _pagos_traslado_p.csv   # IVA a nivel pago
│   ├── _pagos_traslado_dr.csv  # IVA a nivel documento
│   ├── _pagos_retencion_p.csv
│   └── _pagos_retencion_dr.csv
│
├── Reportes Especiales
│   ├── _pagos_detalles_pue.csv # Para cálculo IVA PUE ⭐
│   └── _pagos_detalles_ppd.csv # Para cálculo IVA PPD ⭐
│
├── Impuestos Locales
│   ├── _retencion_local.csv
│   └── _traslado_local.csv
│
├── Complementos Especiales
│   ├── _nomina_general.csv     # Nómina 1.2
│   ├── _nomina_empleado.csv
│   ├── _nomina_percepciones.csv
│   ├── _nomina_deducciones.csv
│   ├── _cartaporte_general.csv # Carta Porte 3.0
│   └── _cartaporte_ubicaciones.csv
│
└── _ledger.csv                 # Registro universal (todo)
```

#### Índices de Relación

| Índice | Descripción | Ejemplo |
|--------|-------------|---------|
| **UUID** | Identificador del CFDI | `ABC12345-1234-1234-1234-123456789012` |
| **ConceptoIndex** | Número de artículo (1, 2, 3...) | `1` |
| **PagoIndex** | Número de pago en complemento | `1` |
| **DoctoIndex** | Documento dentro del pago | `1` |
| **LocalIndex** | Impuesto dentro del nivel | `1` |

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
├── index.html              # Demo interactivo principal (requiere login)
├── README.md               # Esta documentación
│
├── descarga/
│   ├── sat_extractor.py    # Clase principal de descarga masiva
│   └── settings.py         # Configuración (rutas, tiempos, etc.)
│
├── aplanamiento/
│   ├── 1a.py               # Python: XML → DataFrame largo
│   ├── 2a.py               # Python: Pivoteo y mapeo
│   ├── cfdi_m038_logic.cpp # C++: Extractor ultra-rápido
│   ├── cfdi_base.hpp       # C++: Utilidades base
│   ├── cfdi_reporters.hpp  # C++: Writers de CSV
│   └── cfdi_report_defs.hpp # C++: Estructuras de datos
│
└── calculo/
    ├── calc_acreditable_pue.py  # IVA acreditable PUE
    ├── calc_acreditable_ppd.py  # IVA acreditable PPD
    ├── calc_trasladado_pue.py   # IVA trasladado PUE
    ├── calc_trasladado_ppd.py   # IVA trasladado PPD
    └── fusion_final.py          # Consolidación de resultados
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
