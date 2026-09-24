# LEVANTAMIENTO TÉCNICO & MATRIZ DE PREGUNTAS
## Proyecto: Datamart y Plataforma de Talento Humano – Maaji
### Procesos de Compensación (Lina Marcela Builes & Mónica Henao)

---

## 1. RESUMEN DEL ANÁLISIS DEL VIDEO (Lina Builes - Compensación)

Del video **`Videos DataMar_ Compensación.mp4`** se identificaron 3 procesos mensuales con alta carga operativa manual:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. INFORME MENSUAL DE ACTIVOS, INGRESOS Y RETIRADOS                                   │
│    • Exportador de Buk filtrado por quincena (16 al 31).                              │
│    • División manual en 3 pestañas: Activos, Retirados e Ingresos.                     │
│    • Envío en los primeros 2-3 días del mes a líderes y áreas de soporte.              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. SALDOS DE VACACIONES POR LÍDER / SUPERVISOR (Mayor Dolor Operativo)                 │
│    • Descarga reporte de Buk "Saldos Vacaciones".                                      │
│    • Segmentación manual por Empresa (Mas / Armo) y luego por Líder/Supervisor.        │
│    • Ordenamiento de colaboradores por mayor saldo acumulado (>15-20 días).           │
│    • Copiado y pegado de tablas en correos individuales para cada líder en Outlook.   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. INFORME DE REFERIDOS / NOVEDADES PARA TI (Creación/Inactivación de Cuentas)         │
│    • Plantilla mensual solicitada por Tecnología (Excel).                             │
│    • Copiado manual de Ingresos y Retiros para altas/bajas de correos y accesos.      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. OPORTUNIDADES INMEDIATAS DE AUTOMATIZACIÓN

1. **Módulo Automatizado de Saldos de Vacaciones por Líder:**
   - La plataforma ya puede segmentar automáticamente los colaboradores por su `supervisor_id` / líder.
   - En la web, cada líder podrá ver solo su equipo y el semáforo de vacaciones (Verde: <15 días, Naranja: 15-20 días, Rojo: >20 días críticos).
   - Generación y envío automático de correos o alertas por Teams sin que Lina tenga que filtrar y copiar tablas a mano.

2. **Módulo de Novedades para TI (Altas y Bajas):**
   - Generación automática del archivo mensual de altas y bajas en el formato exacto que pide Tecnología (`Tipo Doc`, `Documento`, `Nombre`, `Apellido`, `Correo`, `Movimiento`).

3. **Consolidado de Activos / Retiros / Ingresos:**
   - 100% resuelto con la API de Buk en tiempo real.

---

## 3. DOCUMENTO DE PREGUNTAS Y VALIDACIONES PARA EL EQUIPO

Puedes compartir directamente esta sección con Lina y Mónica para validar detalles clave:

---

### 📋 CUESTIONARIO DE VALIDACIÓN – TALENTO HUMANO & COMPENSACIÓN

#### A. Sobre el Informe de Saldos de Vacaciones por Líder
1. **Periodicidad y Destinatarios:** ¿A cuántos líderes aproximadamente se les envía este correo actualmente y con qué periodicidad ideal les gustaría que se les notifique (mensual o quincenal)?
2. **Umbral de Alerta:** ¿A partir de cuántos días de vacaciones acumuladas consideran que un colaborador entra en estado crítico (ej. > 15 días o > 20 días)?
3. **Canal de Notificación:** ¿Prefieren que el sistema envíe un correo automatizado a cada líder con su tabla, o que el líder ingrese a la plataforma web y vea su semáforo de equipo en vivo?

#### B. Sobre la Base de Temporales (Obra y Labor)
1. **Ubicación y Actualización:** ¿En qué carpeta de OneDrive/SharePoint se guarda el archivo mensual de temporales de Mas y Armo y quién lo actualiza?
2. **Campos mínimos:** ¿Cuáles son las columnas indispensables que se extraen de ese archivo (Cédula, Salario, Fecha Ingreso, Tarifa ARL)?

#### C. Sobre Comisiones y Horas Extras
1. **Sábana de Conceptos:** En Buk, ¿la sábana de conceptos se genera consolidada el último día del mes con ambas quincenas (1Q y 2Q), o se descarga una por cada quincena?
2. **Validación de Totales:** Además del valor total de comisiones en pesos, ¿se requiere algún desglose por tipo de tienda / canal (Retail vs Wholesale)?

#### D. Sobre el Informe para Tecnología (Referidos / Novedades)
1. **Formato TI:** ¿El área de TI requiere el informe exactamente el día 1 de cada mes o en fechas intermedias según los ingresos?
2. **Atributos:** ¿El correo corporativo asignado se genera antes o después de este informe?
