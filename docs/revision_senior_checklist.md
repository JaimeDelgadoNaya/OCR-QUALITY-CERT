# Checklist accionable de revisión senior — `split_and_rename.py`

## 1) Cómo funciona hoy el script (OCR, extracción, grouping, naming)

- [ ] **OCR (decisión previa por muestreo):**
  - Muestra páginas y calcula calidad de texto (`text_quality_score`) y señales de “certificado”.
  - Según ratio de aciertos/ruido, decide `none`, `skip`, `redo` o `force` para OCRmyPDF.
  - Si OCR falla por toolchain (tesseract/ghostscript), aborta con error.

- [ ] **Extracción de datos por página:**
  - Construye texto “combo” (full page + zonas header/top-right/mid/bottom).
  - Certificado: usa regex y scoring por candidatos (CT####, CERT####, labels tipo Certificate/Zeugnis, No: ####/##, etc.).
  - Colada/Heat: extrae por etiquetas (`HEAT`, `COLADA`, `SCHMELZE`, etc.), lookahead de tabla y filtrado de ruido.
  - Normaliza IDs para comparar (`normalize_id_for_compare`) pero preserva `raw` para naming.

- [ ] **Grouping/split por páginas:**
  - Recorre señales página a página.
  - Si cambia `cert_norm`, abre grupo nuevo.
  - Si falta certificado en página, intenta decidir por continuidad (`Page 2/4`), heat coincidente, `is_cert_like`, o la manda a `orphans`.
  - Al final, adjunta huérfanas al siguiente o al último grupo según contexto.

- [ ] **Naming por grupo:**
  - Toma “moda” de certificado y colada del grupo.
  - Construye nombre con plantilla: `cert(prov)_desc_norma_sf_dnmm_dnin_colada.pdf`.
  - Sanitiza caracteres inválidos y recorta por longitud máxima.

---

## 2) 5 fallos probables que explican splits/nombres incorrectos

- [ ] **Fallo 1 — Regex de certificado incompleta para variantes reales multilingües.**
  - Riesgo: certificados con `Cert. No.`, `Certificate No`, `3.1 No`, `Zeugnis Nr:` o `N°` sin slash no entran al scoring alto.
  - Efecto: página se queda sin `cert_norm` y se agrupa por heurística débil (o huérfana).

- [ ] **Fallo 2 — Selección de candidato por score+longitud puede premiar falsos positivos largos.**
  - Hoy `pick_best` ordena por `(score, len(valor))`.
  - Un token largo con dígitos (p.ej. referencia de pedido/documento) puede ganar frente al número de certificado real.

- [ ] **Fallo 3 — Páginas anexo/CE sin campos clave no heredan bien contexto previo/siguiente.**
  - Si una página no trae cert ni heat, cae en lógica de `orphans` y se “pega” por política, no por evidencia semántica robusta.
  - Efecto típico: anexos mezclados en certificado equivocado.

- [ ] **Fallo 4 — Heat con múltiples valores en una misma página no se modela como conjunto.**
  - Flujo actual usa `heat_norm` único (best candidate).
  - Si el certificado cubre dos coladas (tabla de líneas), la reducción a un único valor puede provocar split y rename erróneo.

- [ ] **Fallo 5 — Normalización insuficiente entre variantes equivalentes del mismo ID.**
  - Ejemplos: `00012345/1` vs `12345/1`, `CT 00123456` vs `CT00123456`, `No. 4820-5` vs `4820/5`.
  - Sin normalización canónica por tipo, aparecen grupos duplicados para un mismo certificado.

---

## 3) Plan de cambios en 3 fases

### Fase A — Quick wins (1–2 días)

- [ ] Ampliar regex/labels de **certificado** y **heat** (ver sección 4).
- [ ] Añadir **normalizador canónico de certificado**:
  - elimina separadores espurios,
  - conserva prefijos relevantes (`CT`, `CERT`),
  - opción configurable para mantener/quitar ceros a la izquierda según patrón.
- [ ] Mejorar `pick_best` con penalizaciones:
  - bajar score si token coincide con patrones de `Order`, `Item`, `Delivery`, `Article`, `Document` no certificado.
- [ ] Añadir regla “anexo probable”:
  - si `is_cert_like` o contiene `EN 10204`, y no tiene IDs, hereda `cert_id` del grupo activo.

### Fase B — Refactor medio (3–5 días)

- [ ] Introducir `PageSignature` explícita:
  - `cert_id`, `cert_conf`, `heat_set`, `heat_conf`, `page_ratio`, `is_annex_like`, `language_hits`, `source_spans`.
- [ ] Separar extracción en pipeline:
  1. `collect_candidates` (con spans/contexto),
  2. `rank_candidates`,
  3. `normalize_and_validate`.
- [ ] Reescribir grouping con máquina de estados:
  - estado por `active_cert`, `active_heat_set`, `pending_annex_pages`.
  - reglas de cierre/apertura de grupo explícitas y testeables.
- [ ] Añadir `audit.csv` con motivo de decisión por página (por qué entró/salió de grupo).

### Fase C — Mejoras avanzadas (1–2 semanas)

- [ ] Entrenar/ajustar **scorer híbrido** (reglas + ML liviano) para distinguir cert_id vs document/order IDs.
- [ ] Detección por layout (bloques/tabla) para heat multivalor y correspondencia con líneas de producto.
- [ ] Modo de validación cruzada:
  - compara firmas entre páginas adyacentes,
  - detecta saltos improbables y propone corrección automática.
- [ ] Banco de pruebas con PDFs reales anonimizados + métricas:
  - `split_accuracy`, `filename_accuracy`, `orphan_rate`, `false_merge_rate`.

---

## 4) Patrones/labels multilingües que faltan (exactamente qué añadir)

### 4.1 Número de certificado

- [ ] **Labels faltantes recomendados (case-insensitive):**
  - `Cert\.?\s*(No\.?|Nr\.?|Nº|N°)`
  - `Certificate\s*(No\.?|Number)`
  - `Certificado\s*(Nº|N°|No\.?|Número)`
  - `N[º°o\.]\s*:?` (genérico, solo con contexto de certificado)
  - `Zeugnis\s*[- ]?(Nr\.?|Nummer)`
  - `Prüfbescheinigung\s*(Nr\.?|Nummer)`
  - `Inspection\s*Certificate\s*(No\.?|Nr\.?)`
  - `Mill\s*Test\s*(Certificate\s*)?(No\.?|Nr\.?)`
  - `3\.1\s*(Certificate\s*)?(No\.?|Nr\.?)`
  - `Document\s*(No\.?|Nr\.?)` (solo con contexto EN10204/certificate)

- [ ] **Formatos de valor que hay que soportar:**
  - solo dígitos con ceros iniciales: `0000369904`
  - dígitos + sufijo: `0000369904/1`, `4820/5`, `4820-5`
  - prefijo alfanumérico: `CT00123456`, `CERT25007297`, `MTC-2024-001234`
  - mixtos con separadores: `AB/2024/000123`, `A-000123-24`

- [ ] **Regex base sugerida (valor):**
  - `(?P<cert>(?:CT|CERT|MTC)?[A-Z0-9]{2,}(?:[\/-][A-Z0-9]{1,}){0,3})`
  - aplicar validación posterior para evitar capturar códigos de artículo.

### 4.2 Colada / Heat

- [ ] **Labels faltantes recomendados (case-insensitive):**
  - `Heat\s*(No\.?|Number|#)`
  - `Melt\s*(No\.?|Number|#)`
  - `Cast\s*(No\.?|Number|#)`
  - `Batch\s*(No\.?|Number|#)`
  - `Lot\s*(No\.?|Number|#)`
  - `Colada\s*(No\.?|Nº|N°)?`
  - `Colata\s*(N\.?|Nr\.?)?`
  - `Schmelze\s*(Nr\.?|Nummer)?`
  - `Charge\s*(No\.?|Nr\.?|N°)?`
  - `Chargen\s*(Nr\.?|Nummer)?`
  - `Coulée\s*(No\.?|N°|Nr\.?)?`

- [ ] **Formatos de valor que hay que soportar:**
  - numérico: `12345`, `001234`
  - alfanumérico: `H23A17`, `A8F9`
  - con slash/guion: `23/771`, `H-2024-77`
  - múltiples heats en una página/tabla (captura como conjunto, no único).

---

## 5) Nuevo algoritmo de “page signature” y grouping

### 5.1 Firma por página (`PageSignature`)

- [ ] Definir:
  - `cert_id_raw`, `cert_id_norm`, `cert_conf`
  - `heat_values_raw: set[str]`, `heat_values_norm: set[str]`, `heat_conf`
  - `page_num`, `page_total`
  - `is_cert_like`, `is_annex_like` (EN10204/CE/Declaration/Annex keywords)
  - `evidence`: lista de matches (regex, zona, línea)

### 5.2 Clave de agrupación

- [ ] Usar clave primaria por página:
  - `group_key = (cert_id_norm or "", frozenset(heat_values_norm))`
- [ ] Reglas:
  - Si `cert_id_norm` existe: ancla grupo por certificado.
  - Si además hay `heat_set` no vacío y `split_within_cert_on_heat_change=True`: subgrupo por heat_set.
  - Si `cert_id_norm` vacío pero `is_annex_like=True`: **heredar** `cert_id_norm` y `heat_set` del grupo activo más cercano compatible.

### 5.3 Herencia para anexos/CE sin dato

- [ ] Backfill/forward-fill controlado:
  - `pass 1` izquierda→derecha: hereda del último grupo activo si no hay conflicto.
  - `pass 2` derecha→izquierda: resuelve huérfanas al grupo siguiente si la similitud textual supera umbral.
- [ ] Criterio de compatibilidad (ejemplo):
  - +2 si coincide `page_total` y secuencia plausible (`2/4`, `3/4`)
  - +2 si `is_cert_like` + keywords comunes del grupo
  - +1 por overlap de tokens técnicos/material
  - asignar al grupo con score mayor, mínimo `>=3`.

### 5.4 Selección de nombre final del grupo

- [ ] `cert_raw` del grupo = candidato con mayor `cert_conf`, no solo moda.
- [ ] `heat_raw` del grupo:
  - si 1 valor: ese;
  - si varios: concatenar estable (`H1+H2`) o plantilla configurable (`MULTIHEAT`).
- [ ] Añadir `confidence_group` y bandera `needs_review` cuando cert/heat se hereden sin evidencia directa.

---

## Definición de “done” (operativa)

- [ ] 95%+ de páginas con `group_key` no vacío o heredado con justificación.
- [ ] 0 splits por cambio espurio de formato del mismo cert (`000123/1` vs `123/1`).
- [ ] 0 renames con IDs de pedido/artículo en lugar de cert.
- [ ] Reporte por PDF con trazabilidad por página (qué regex ganó y por qué).
