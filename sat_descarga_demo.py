#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAT DESCARGA DEMO - Script Interactivo de Descarga Masiva
=========================================================

Este script se conecta al SAT real para descargar CFDIs.
Diseñado para documentar el proceso en https://srexcel.github.io/tax/

USO:
    python sat_descarga_demo.py

REQUISITOS:
    pip install cfdiclient lxml cryptography requests

AUTOR: Cesar - Sistema de Recuperación de IVA
"""

import os
import sys
import json
import time
import base64
import zipfile
import io
from pathlib import Path
from datetime import datetime, timedelta
from getpass import getpass
from typing import Optional, Dict, List, Any

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

CONFIG_FILE = Path.home() / ".sat_descarga_config.json"
DEFAULT_OUTPUT_DIR = Path.home() / "SAT_Descargas"

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def color(text: str, c: str) -> str:
    """Aplica color al texto."""
    return f"{c}{text}{Colors.END}"

def print_header():
    """Imprime el header del programa."""
    print()
    print(color("=" * 70, Colors.CYAN))
    print(color("  🇲🇽 SAT DESCARGA DEMO - Conexión Real al SAT", Colors.BOLD))
    print(color("  Sistema de Recuperación de IVA", Colors.CYAN))
    print(color("=" * 70, Colors.CYAN))
    print()

def print_step(step: int, total: int, message: str):
    """Imprime un paso del proceso."""
    print(f"\n{color(f'[{step}/{total}]', Colors.BLUE)} {color(message, Colors.BOLD)}")
    print(color("-" * 50, Colors.BLUE))

def print_success(message: str):
    print(f"  {color('✅', Colors.GREEN)} {message}")

def print_error(message: str):
    print(f"  {color('❌', Colors.RED)} {message}")

def print_warning(message: str):
    print(f"  {color('⚠️', Colors.YELLOW)} {message}")

def print_info(message: str):
    print(f"  {color('ℹ️', Colors.CYAN)} {message}")

def print_progress(message: str):
    print(f"  {color('⏳', Colors.YELLOW)} {message}")

# ==============================================================================
# GESTIÓN DE CONFIGURACIÓN
# ==============================================================================

def load_config() -> Dict:
    """Carga la configuración guardada."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config: Dict):
    """Guarda la configuración."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print_warning(f"No se pudo guardar config: {e}")

def get_default_dates() -> tuple:
    """Retorna fechas default: primer día del mes anterior hasta hoy."""
    today = datetime.now()
    first_of_this_month = today.replace(day=1)
    last_month = first_of_this_month - timedelta(days=1)
    first_of_last_month = last_month.replace(day=1)
    return first_of_last_month, today

# ==============================================================================
# INTERFAZ DE USUARIO
# ==============================================================================

def input_with_default(prompt: str, default: str = "") -> str:
    """Input con valor por defecto."""
    if default:
        result = input(f"  {prompt} [{color(default, Colors.CYAN)}]: ").strip()
        return result if result else default
    else:
        return input(f"  {prompt}: ").strip()

def input_date(prompt: str, default: datetime) -> datetime:
    """Input de fecha con validación."""
    default_str = default.strftime("%Y-%m-%d")
    while True:
        date_str = input_with_default(prompt, default_str)
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print_error("Formato inválido. Usa YYYY-MM-DD")

def input_choice(prompt: str, options: List[str], default: int = 0) -> int:
    """Input de selección múltiple."""
    print(f"\n  {prompt}")
    for i, opt in enumerate(options):
        marker = color("→", Colors.GREEN) if i == default else " "
        print(f"    {marker} [{i+1}] {opt}")
    
    while True:
        choice = input(f"  Selección [{default+1}]: ").strip()
        if not choice:
            return default
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return idx
        except ValueError:
            pass
        print_error(f"Selección inválida. Elige 1-{len(options)}")

def input_path(prompt: str, default: str, must_exist: bool = True) -> Path:
    """Input de ruta de archivo."""
    while True:
        path_str = input_with_default(prompt, default)
        path = Path(path_str).expanduser()
        
        if must_exist and not path.exists():
            print_error(f"Archivo no encontrado: {path}")
            continue
        
        return path

def confirm(prompt: str, default: bool = True) -> bool:
    """Confirmación sí/no."""
    options = "[S/n]" if default else "[s/N]"
    response = input(f"  {prompt} {options}: ").strip().lower()
    
    if not response:
        return default
    return response in ('s', 'si', 'sí', 'y', 'yes')

# ==============================================================================
# CLASE PRINCIPAL
# ==============================================================================

class SATDescargaDemo:
    """Clase principal para descarga de CFDIs del SAT."""
    
    def __init__(self):
        self.config = load_config()
        self.fiel = None
        self.token = None
        self.rfc = ""
        self.output_dir = DEFAULT_OUTPUT_DIR
        
        # Estadísticas
        self.stats = {
            'solicitudes_enviadas': 0,
            'paquetes_descargados': 0,
            'xmls_extraidos': 0,
            'errores': 0
        }
    
    def verificar_dependencias(self) -> bool:
        """Verifica que las dependencias estén instaladas."""
        print_step(1, 6, "Verificando dependencias")
        
        dependencias = {
            'cfdiclient': 'cfdiclient',
            'lxml': 'lxml',
            'cryptography': 'cryptography',
            'requests': 'requests'
        }
        
        faltantes = []
        
        for nombre, paquete in dependencias.items():
            try:
                __import__(nombre)
                print_success(f"{nombre} instalado")
            except ImportError:
                print_error(f"{nombre} NO instalado")
                faltantes.append(paquete)
        
        if faltantes:
            print()
            print_warning("Instala las dependencias faltantes con:")
            print(f"    {color(f'pip install {\" \".join(faltantes)}', Colors.YELLOW)}")
            return False
        
        return True
    
    def configurar_fiel(self) -> bool:
        """Configura la FIEL del usuario."""
        print_step(2, 6, "Configuración de FIEL")
        
        # RFC
        default_rfc = self.config.get('last_rfc', '')
        self.rfc = input_with_default("RFC del contribuyente", default_rfc).upper()
        
        if not self.rfc:
            print_error("RFC es requerido")
            return False
        
        # Buscar archivos FIEL
        default_fiel_dir = self.config.get('last_fiel_dir', str(Path.home()))
        
        print_info(f"Buscando archivos FIEL para {self.rfc}...")
        
        # Intentar encontrar automáticamente
        possible_dirs = [
            Path(default_fiel_dir),
            Path.home() / "FIEL",
            Path.home() / "fiel",
            Path.home() / self.rfc / "FIEL",
            Path.home() / "Documents" / "FIEL",
            Path(f"Z:/Respaldo/Nuevo vol/Otras/{self.rfc[:3]}*/FIEL"),  # Tu estructura
        ]
        
        cer_path = None
        key_path = None
        
        # Preguntar directorio
        fiel_dir = input_path(
            "Directorio de archivos FIEL (.cer y .key)",
            default_fiel_dir,
            must_exist=True
        )
        
        # Buscar .cer
        cer_files = list(fiel_dir.glob("*.cer"))
        if cer_files:
            if len(cer_files) == 1:
                cer_path = cer_files[0]
                print_success(f"Certificado encontrado: {cer_path.name}")
            else:
                print_info(f"Múltiples certificados encontrados:")
                for i, f in enumerate(cer_files):
                    print(f"    [{i+1}] {f.name}")
                idx = input_choice("Selecciona el certificado", [f.name for f in cer_files])
                cer_path = cer_files[idx]
        else:
            cer_path = input_path("Ruta al archivo .cer", "", must_exist=True)
        
        # Buscar .key
        key_files = list(fiel_dir.glob("*.key"))
        if key_files:
            if len(key_files) == 1:
                key_path = key_files[0]
                print_success(f"Llave privada encontrada: {key_path.name}")
            else:
                print_info(f"Múltiples llaves encontradas:")
                idx = input_choice("Selecciona la llave", [f.name for f in key_files])
                key_path = key_files[idx]
        else:
            key_path = input_path("Ruta al archivo .key", "", must_exist=True)
        
        # Contraseña
        print()
        password = getpass(f"  🔑 Contraseña de la llave privada: ")
        
        if not password:
            print_error("Contraseña es requerida")
            return False
        
        # Cargar FIEL
        print_progress("Cargando FIEL...")
        
        try:
            from cfdiclient import Fiel
            
            with open(cer_path, 'rb') as f:
                cer_data = f.read()
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            self.fiel = Fiel(cer_data, key_data, password)
            print_success("FIEL cargada correctamente")
            
            # Guardar config
            self.config['last_rfc'] = self.rfc
            self.config['last_fiel_dir'] = str(fiel_dir)
            save_config(self.config)
            
            return True
            
        except Exception as e:
            print_error(f"Error cargando FIEL: {e}")
            print_info("Verifica que la contraseña sea correcta")
            return False
    
    def autenticar(self) -> bool:
        """Obtiene token de autenticación del SAT."""
        print_step(3, 6, "Autenticación con el SAT")
        
        print_progress("Conectando al servicio de autenticación...")
        
        try:
            from cfdiclient import Autenticacion
            
            auth = Autenticacion(self.fiel)
            self.token = auth.obtener_token()
            
            if self.token:
                print_success("¡Autenticación exitosa!")
                print_info(f"Token: {self.token[:50]}...")
                return True
            else:
                print_error("No se obtuvo token")
                return False
                
        except Exception as e:
            print_error(f"Error de autenticación: {e}")
            return False
    
    def configurar_descarga(self) -> Dict:
        """Configura los parámetros de descarga."""
        print_step(4, 6, "Configuración de descarga")
        
        # Fechas
        fecha_inicio_default, fecha_fin_default = get_default_dates()
        
        print_info("Período de descarga:")
        fecha_inicio = input_date("Fecha inicial (YYYY-MM-DD)", fecha_inicio_default)
        fecha_fin = input_date("Fecha final (YYYY-MM-DD)", fecha_fin_default)
        
        # Validar rango
        if fecha_inicio > fecha_fin:
            print_warning("Fecha inicial mayor que final, intercambiando...")
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
        
        dias = (fecha_fin - fecha_inicio).days
        print_info(f"Período: {dias} días")
        
        if dias > 31:
            print_warning(f"Período largo ({dias} días). Se dividirá en solicitudes de 7 días.")
        
        # Tipo de descarga
        tipo_descarga_idx = input_choice(
            "Tipo de descarga:",
            ["Metadata (rápido, solo info básica)", "CFDI (XMLs completos)"],
            default=0
        )
        tipo_descarga = "Metadata" if tipo_descarga_idx == 0 else "CFDI"
        
        # Tipo de CFDI
        tipo_cfdi_idx = input_choice(
            "Tipo de comprobantes:",
            ["Recibidos (compras)", "Emitidos (ventas)"],
            default=0
        )
        tipo_cfdi = "RECEIVED" if tipo_cfdi_idx == 0 else "ISSUED"
        
        # Directorio de salida
        default_output = self.config.get('last_output_dir', str(DEFAULT_OUTPUT_DIR))
        output_str = input_with_default("Directorio de salida", default_output)
        self.output_dir = Path(output_str).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config['last_output_dir'] = str(self.output_dir)
        save_config(self.config)
        
        print_success(f"Salida: {self.output_dir}")
        
        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'tipo_descarga': tipo_descarga,
            'tipo_cfdi': tipo_cfdi
        }
    
    def dividir_periodos(self, inicio: datetime, fin: datetime, dias: int = 7) -> List[tuple]:
        """Divide un rango de fechas en sub-rangos."""
        rangos = []
        actual = inicio
        
        while actual <= fin:
            fin_rango = min(actual + timedelta(days=dias - 1), fin)
            rangos.append((actual, fin_rango))
            actual = fin_rango + timedelta(days=1)
        
        return rangos
    
    def ejecutar_descarga(self, config: Dict) -> bool:
        """Ejecuta el proceso de descarga."""
        print_step(5, 6, "Ejecutando descarga")
        
        from cfdiclient import (
            SolicitaDescargaEmitidos,
            SolicitaDescargaRecibidos,
            VerificaSolicitudDescarga,
            DescargaMasiva
        )
        
        # Dividir en períodos
        rangos = self.dividir_periodos(
            config['fecha_inicio'],
            config['fecha_fin']
        )
        
        print_info(f"Se generarán {len(rangos)} solicitud(es)")
        
        solicitudes = []
        
        # Enviar solicitudes
        for i, (inicio, fin) in enumerate(rangos, 1):
            print(f"\n  📤 Solicitud {i}/{len(rangos)}: {inicio.date()} → {fin.date()}")
            
            try:
                # Seleccionar servicio
                if config['tipo_cfdi'] == 'ISSUED':
                    service = SolicitaDescargaEmitidos(self.fiel)
                    kwargs = {'rfc_emisor': self.rfc}
                else:
                    service = SolicitaDescargaRecibidos(self.fiel)
                    kwargs = {'rfc_receptor': self.rfc}
                
                # Enviar solicitud
                response = service.solicitar_descarga(
                    self.token,
                    self.rfc,
                    inicio,
                    fin,
                    tipo_solicitud=config['tipo_descarga'],
                    **kwargs
                )
                
                cod = response.get('cod_estatus', 'N/A')
                msg = response.get('mensaje', '')
                rid = response.get('id_solicitud')
                
                if rid:
                    print_success(f"ID: {rid}")
                    solicitudes.append({
                        'id': rid,
                        'inicio': inicio,
                        'fin': fin,
                        'status': 1
                    })
                    self.stats['solicitudes_enviadas'] += 1
                else:
                    print_error(f"Sin ID - cod={cod} msg={msg}")
                    self.stats['errores'] += 1
                
                # Esperar entre solicitudes
                if i < len(rangos):
                    time.sleep(2)
                    
            except Exception as e:
                print_error(f"Error: {e}")
                self.stats['errores'] += 1
        
        if not solicitudes:
            print_error("No se generaron solicitudes válidas")
            return False
        
        # Monitorear y descargar
        print(f"\n  ⏳ Monitoreando {len(solicitudes)} solicitud(es)...")
        
        verifier = VerificaSolicitudDescarga(self.fiel)
        downloader = DescargaMasiva(self.fiel)
        
        pendientes = list(solicitudes)
        intentos = 0
        max_intentos = 30  # 30 minutos máximo
        
        while pendientes and intentos < max_intentos:
            intentos += 1
            nuevos_pendientes = []
            
            for sol in pendientes:
                try:
                    print(f"\n  🔍 Verificando {sol['id'][:12]}...")
                    
                    response = verifier.verificar_descarga(
                        self.token,
                        self.rfc,
                        sol['id']
                    )
                    
                    estado = int(response.get('estado_solicitud', -1))
                    msg = response.get('mensaje', '')
                    
                    if estado == 1:
                        print_info(f"Estado: Aceptada - {msg}")
                        nuevos_pendientes.append(sol)
                        
                    elif estado == 2:
                        print_info(f"Estado: En proceso - {msg}")
                        nuevos_pendientes.append(sol)
                        
                    elif estado == 3:
                        print_success(f"Estado: ¡Lista para descarga!")
                        paquetes = response.get('paquetes') or []
                        
                        if paquetes:
                            print_info(f"Paquetes disponibles: {len(paquetes)}")
                            self.descargar_paquetes(downloader, paquetes)
                        else:
                            print_warning("Sin paquetes (período sin CFDIs)")
                            
                    elif estado in (4, 5):
                        print_error(f"Estado: Error/Rechazada - {msg}")
                        self.stats['errores'] += 1
                        
                    else:
                        print_warning(f"Estado desconocido: {estado}")
                        nuevos_pendientes.append(sol)
                        
                except Exception as e:
                    print_error(f"Error verificando: {e}")
                    nuevos_pendientes.append(sol)
            
            pendientes = nuevos_pendientes
            
            if pendientes:
                print(f"\n  ⏰ Esperando 60 segundos... ({len(pendientes)} pendiente(s))")
                print("     (Ctrl+C para cancelar)")
                try:
                    time.sleep(60)
                except KeyboardInterrupt:
                    print_warning("\nCancelado por usuario")
                    break
        
        return True
    
    def descargar_paquetes(self, downloader, paquetes: List[str]):
        """Descarga los paquetes de CFDIs."""
        for i, pkg_id in enumerate(paquetes, 1):
            try:
                print(f"\n    📦 Descargando paquete {i}/{len(paquetes)}...")
                
                zip_path = self.output_dir / f"{pkg_id}.zip"
                
                if zip_path.exists():
                    print_warning(f"Ya existe: {zip_path.name}")
                    self.stats['paquetes_descargados'] += 1
                    continue
                
                response = downloader.descargar_paquete(
                    self.token,
                    self.rfc,
                    pkg_id
                )
                
                if response.get('paquete_b64'):
                    data = base64.b64decode(response['paquete_b64'])
                    size_kb = len(data) / 1024
                    
                    with open(zip_path, 'wb') as f:
                        f.write(data)
                    
                    print_success(f"Guardado: {zip_path.name} ({size_kb:.1f} KB)")
                    self.stats['paquetes_descargados'] += 1
                    
                    # Contar XMLs
                    try:
                        with zipfile.ZipFile(io.BytesIO(data)) as z:
                            xmls = [f for f in z.namelist() if f.endswith('.xml')]
                            self.stats['xmls_extraidos'] += len(xmls)
                            print_info(f"Contenido: {len(xmls)} XMLs")
                    except:
                        pass
                else:
                    cod = response.get('cod_estatus', 'N/A')
                    msg = response.get('mensaje', '')
                    print_error(f"Sin datos - cod={cod} msg={msg}")
                    
            except Exception as e:
                print_error(f"Error descargando: {e}")
    
    def mostrar_resumen(self):
        """Muestra el resumen final."""
        print_step(6, 6, "Resumen")
        
        print(f"""
  {color('📊 Estadísticas:', Colors.BOLD)}
  
     Solicitudes enviadas:  {self.stats['solicitudes_enviadas']}
     Paquetes descargados:  {self.stats['paquetes_descargados']}
     XMLs extraídos:        {self.stats['xmls_extraidos']}
     Errores:               {self.stats['errores']}
     
  {color('📁 Archivos guardados en:', Colors.BOLD)}
     {self.output_dir}
        """)
        
        # Listar archivos
        zips = list(self.output_dir.glob("*.zip"))
        if zips:
            print(f"  {color('Archivos ZIP:', Colors.CYAN)}")
            for z in zips[:10]:
                size = z.stat().st_size / 1024
                print(f"     • {z.name} ({size:.1f} KB)")
            if len(zips) > 10:
                print(f"     ... y {len(zips) - 10} más")
    
    def ejecutar(self):
        """Ejecuta el flujo completo."""
        print_header()
        
        # Paso 1: Verificar dependencias
        if not self.verificar_dependencias():
            return
        
        # Paso 2: Configurar FIEL
        if not self.configurar_fiel():
            return
        
        # Paso 3: Autenticar
        if not self.autenticar():
            return
        
        # Paso 4: Configurar descarga
        config = self.configurar_descarga()
        
        # Confirmar
        print()
        print(color("  Resumen de configuración:", Colors.BOLD))
        print(f"     RFC:           {self.rfc}")
        print(f"     Período:       {config['fecha_inicio'].date()} → {config['fecha_fin'].date()}")
        print(f"     Tipo:          {config['tipo_descarga']}")
        print(f"     Comprobantes:  {'Recibidos' if config['tipo_cfdi'] == 'RECEIVED' else 'Emitidos'}")
        print(f"     Salida:        {self.output_dir}")
        print()
        
        if not confirm("¿Iniciar descarga?"):
            print_warning("Cancelado por usuario")
            return
        
        # Paso 5: Ejecutar
        self.ejecutar_descarga(config)
        
        # Paso 6: Resumen
        self.mostrar_resumen()
        
        print()
        print(color("  ¡Proceso completado!", Colors.GREEN))
        print(color("  Siguiente paso: Aplanar los XMLs para procesamiento", Colors.CYAN))
        print()


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    try:
        demo = SATDescargaDemo()
        demo.ejecutar()
    except KeyboardInterrupt:
        print("\n\n  Cancelado por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n  Error fatal: {e}")
        sys.exit(1)
