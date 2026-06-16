interface ReportesVistaProps {
  comisionId: string;
}

/**
 * Vista de reportes rápidos con métricas de la materia.
 * TODO: (REVIEW) Reportes endpoint /api/reportes/materia/:materiaId requires materia_id.
 * comisionId does not map directly to materia_id without a comision→materia lookup.
 * Showing informative state until the mapping is resolved.
 */
export default function ReportesVista({ comisionId: _comisionId }: ReportesVistaProps) {
  // TODO: (FEAT) Derive materia_id from comisionId once /api/comisiones endpoint exists
  // and call useReporteMateria(materiaId). For now show placeholder state.

  return (
    <div role="status" className="p-4 bg-blue-50 rounded border border-blue-200 text-sm text-blue-700">
      Seleccioná una comisión con actividades configuradas para ver los reportes rápidos.
    </div>
  );
}
