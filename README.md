# OCR-QUALITY-CERT

Script para separar y renombrar PDFs de certificados usando **PyMuPDF** con fallback de **ocrmypdf**.

## Ejecutar GUI

```bash
python split_and_rename.py
```

Opciones nuevas en GUI:
- **Forzar OCR siempre**
- **Modo debug**

## Ejecutar tests

```bash
pytest -q
```

## Añadir vendors / plantilla de nombres

Editar `Config.vendor_templates` en `certsplit/config.py`.

Plantilla por defecto:

```text
{cert}({vendor})_{desc}_{norma}_{sf}_{dn_mm}_{dn_in}_{heats}.pdf
```

Variables disponibles: `cert`, `vendor`, `desc`, `norma`, `sf`, `dn_mm`, `dn_in`, `heats`.

## Patrones de extracción

Los patrones de certificado/colada están en `certsplit/extraction.py` (`CERT_LABEL_RE`, `CERT_FALLBACK_RE`, `HEAT_LABEL_RE`).
