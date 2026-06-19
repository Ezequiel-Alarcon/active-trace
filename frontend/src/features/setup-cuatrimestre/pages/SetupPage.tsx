import { useReducer, useState } from 'react';
import { PageHeader, Button, Card } from '@/shared/ui';
import { setupReducer, INITIAL_SETUP_STATE, PASOS } from '../types/setup';
import WizardProgress from '../components/WizardProgress';
import type { SetupState } from '../types/setup';

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full';

export default function SetupPage() {
  const [state, dispatch] = useReducer(setupReducer, INITIAL_SETUP_STATE);
  const { step } = state;
  const [showConfirmCancel, setShowConfirmCancel] = useState(false);
  const [cohorteNombre, setCohorteNombre] = useState('');
  const [cohorteCarrera, setCohorteCarrera] = useState('');
  const [cohorteAnio, setCohorteAnio] = useState('');
  const [clonarOrigen, setClonarOrigen] = useState('');
  const [clonarDestino, setClonarDestino] = useState('');
  const [programasFile, setProgramasFile] = useState<File | null>(null);
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [fechaEvaluaciones, setFechaEvaluaciones] = useState('');
  const [avisoTitulo, setAvisoTitulo] = useState('');
  const [avisoCuerpo, setAvisoCuerpo] = useState('');

  function handleNext() {
    switch (step) {
      case 0:
        dispatch({ type: 'SET_COHORTE', data: { nombre: cohorteNombre, carrera: cohorteCarrera, anio: cohorteAnio } });
        dispatch({ type: 'ADD_RESUMEN', item: `Cohorte "${cohorteNombre}" (${cohorteCarrera} - ${cohorteAnio})` });
        break;
      case 1:
        dispatch({ type: 'SET_CLONAR', data: { origen: clonarOrigen, destino: clonarDestino } });
        dispatch({ type: 'ADD_RESUMEN', item: `Equipo clonado de "${clonarOrigen}" a "${clonarDestino}"` });
        break;
      case 2:
        dispatch({ type: 'ADD_RESUMEN', item: 'Asignaciones ajustadas' });
        break;
      case 3:
        dispatch({ type: 'ADD_RESUMEN', item: 'Vigencias ajustadas' });
        break;
      case 4:
        dispatch({ type: 'SET_PROGRAMAS', data: { archivos: programasFile ? [programasFile.name] : [] } });
        dispatch({ type: 'ADD_RESUMEN', item: `Programas cargados: ${programasFile?.name ?? 'ninguno'}` });
        break;
      case 5:
        dispatch({ type: 'SET_FECHAS', data: { inicio: fechaInicio, fin: fechaFin, evaluaciones: fechaEvaluaciones } });
        dispatch({ type: 'ADD_RESUMEN', item: `Fechas: ${fechaInicio} — ${fechaFin}` });
        break;
      case 6:
        dispatch({ type: 'SET_AVISO', data: { titulo: avisoTitulo, cuerpo: avisoCuerpo } });
        dispatch({ type: 'ADD_RESUMEN', item: `Aviso "${avisoTitulo}" publicado` });
        break;
    }
    dispatch({ type: 'NEXT' });
  }

  function handleCancel() {
    if (confirm('¿Cancelar el setup? Se descartarán los cambios del paso actual.')) {
      dispatch({ type: 'RESET' });
    }
  }

  function handleReset() {
    dispatch({ type: 'RESET' });
  }

  if (step >= PASOS.length) {
    return (
      <div className="flex flex-col gap-4">
        <PageHeader title="Setup completado" />
        <Card>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Resumen de operaciones realizadas</h2>
          <ul className="list-disc pl-5 text-sm text-gray-600 flex flex-col gap-1">
            {state.resumen.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
          <div className="mt-4">
            <Button onClick={handleReset}>Iniciar nuevo setup</Button>
          </div>
        </Card>
      </div>
    );
  }

  function renderStep() {
    switch (step) {
      case 0:
        return (
          <div className="flex flex-col gap-3 max-w-md">
            <h2 className="text-sm font-semibold text-gray-700">Crear cohorte</h2>
            <input value={cohorteNombre} onChange={(e) => setCohorteNombre(e.target.value)} placeholder="Nombre de la cohorte" className={INPUT_CLASS} />
            <input value={cohorteCarrera} onChange={(e) => setCohorteCarrera(e.target.value)} placeholder="Carrera" className={INPUT_CLASS} />
            <input value={cohorteAnio} onChange={(e) => setCohorteAnio(e.target.value)} placeholder="Año" className={INPUT_CLASS} />
          </div>
        );
      case 1:
        return (
          <div className="flex flex-col gap-3 max-w-md">
            <h2 className="text-sm font-semibold text-gray-700">Clonar equipo del período anterior</h2>
            <input value={clonarOrigen} onChange={(e) => setClonarOrigen(e.target.value)} placeholder="Origen (materia/carrera/cohorte)" className={INPUT_CLASS} />
            <input value={clonarDestino} onChange={(e) => setClonarDestino(e.target.value)} placeholder="Destino (materia/carrera/cohorte)" className={INPUT_CLASS} />
          </div>
        );
      case 2:
        return (
          <div className="flex flex-col gap-3 max-w-md">
            <h2 className="text-sm font-semibold text-gray-700">Ajustar asignaciones faltantes</h2>
            <p className="text-sm text-gray-500">Utilice el formulario de asignación masiva en Equipos Docentes.</p>
            <p className="text-xs text-gray-400">Puede volver a esta sección después de completar las asignaciones.</p>
          </div>
        );
      case 3:
        return (
          <div className="flex flex-col gap-3 max-w-md">
            <h2 className="text-sm font-semibold text-gray-700">Ajustar vigencias</h2>
            <p className="text-sm text-gray-500">Utilice el formulario de vigencia en Equipos Docentes.</p>
          </div>
        );
      case 4:
        return (
          <div className="flex flex-col gap-3 max-w-md">
            <h2 className="text-sm font-semibold text-gray-700">Cargar programas de materia</h2>
            <input
              type="file"
              onChange={(e) => setProgramasFile(e.target.files?.[0] ?? null)}
              className="text-sm"
              accept=".pdf,.doc,.docx"
            />
          </div>
        );
      case 5:
        return (
          <div className="flex flex-col gap-3 max-w-md">
            <h2 className="text-sm font-semibold text-gray-700">Cargar fechas académicas</h2>
            <label className="text-sm text-gray-600">Inicio de cursada</label>
            <input value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)} type="date" className={INPUT_CLASS} />
            <label className="text-sm text-gray-600">Fin de cursada</label>
            <input value={fechaFin} onChange={(e) => setFechaFin(e.target.value)} type="date" className={INPUT_CLASS} />
            <label className="text-sm text-gray-600">Fechas de evaluaciones</label>
            <textarea value={fechaEvaluaciones} onChange={(e) => setFechaEvaluaciones(e.target.value)} className={INPUT_CLASS} placeholder="Detalle las fechas de evaluaciones…" />
          </div>
        );
      case 6:
        return (
          <div className="flex flex-col gap-3 max-w-md">
            <h2 className="text-sm font-semibold text-gray-700">Publicar aviso de bienvenida</h2>
            <input value={avisoTitulo} onChange={(e) => setAvisoTitulo(e.target.value)} placeholder="Título del aviso" className={INPUT_CLASS} />
            <textarea value={avisoCuerpo} onChange={(e) => setAvisoCuerpo(e.target.value)} className={`${INPUT_CLASS} min-h-[100px]`} placeholder="Cuerpo del aviso…" />
          </div>
        );
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Setup de Cuatrimestre" />
      <WizardProgress pasos={PASOS} pasoActual={step} />
      <Card>{renderStep()}</Card>
      <div className="flex gap-2">
        {step > 0 && (
          <Button variant="secondary" onClick={() => dispatch({ type: 'PREV' })}>
            Anterior
          </Button>
        )}
        <Button onClick={handleNext}>
          {step < PASOS.length - 1 ? 'Siguiente' : 'Finalizar'}
        </Button>
        <Button variant="secondary" onClick={handleCancel}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}
