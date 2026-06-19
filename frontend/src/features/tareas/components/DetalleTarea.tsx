import { useState } from 'react';
import { useComentarios, useAgregarComentario, useDelegarTarea } from '../hooks/useTareas';
import { Button } from '@/shared/ui';
import type { TareaResponse } from '../types/tareas';

const INPUT_CLASS = 'border border-gray-300 rounded px-3 py-1.5 text-sm w-full';

interface DetalleTareaProps {
  tarea: TareaResponse;
  onClose: () => void;
}

export default function DetalleTarea({ tarea, onClose }: DetalleTareaProps) {
  const [nuevoComentario, setNuevoComentario] = useState('');
  const [docenteDelegar, setDocenteDelegar] = useState('');
  const { data: comentarios, isLoading: loadingCom } = useComentarios(tarea.id);
  const agregarCom = useAgregarComentario(tarea.id);
  const delegar = useDelegarTarea();

  function handleAgregarComentario() {
    if (!nuevoComentario.trim()) return;
    agregarCom.mutate(nuevoComentario, { onSuccess: () => setNuevoComentario('') });
  }

  function handleDelegar() {
    if (!docenteDelegar.trim()) return;
    delegar.mutate({ id: tarea.id, docente_id: docenteDelegar });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto flex flex-col gap-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">{tarea.titulo}</h2>
            <p className="text-sm text-gray-500">{tarea.materia_nombre ?? 'Sin materia'}</p>
          </div>
          <Button variant="secondary" onClick={onClose}>Cerrar</Button>
        </div>

        <p className="text-sm text-gray-700">{tarea.descripcion}</p>

        <div className="text-xs text-gray-500">
          <p>Asignado a: <strong>{tarea.docente_asignado_nombre}</strong></p>
          <p>Asignado por: <strong>{tarea.docente_asignador_nombre}</strong></p>
          <p>Estado: <strong>{tarea.estado}</strong></p>
        </div>

        <div className="border-t border-gray-200 pt-3">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Delegar tarea</h3>
          <div className="flex gap-2">
            <input
              value={docenteDelegar}
              onChange={(e) => setDocenteDelegar(e.target.value)}
              placeholder="ID del docente"
              className={INPUT_CLASS}
            />
            <Button variant="secondary" onClick={handleDelegar} disabled={delegar.isPending}>
              Delegar
            </Button>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-3">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Comentarios</h3>

          {loadingCom && <p className="text-xs text-gray-500">Cargando comentarios…</p>}

          <div className="flex flex-col gap-2 max-h-48 overflow-y-auto mb-3">
            {(comentarios ?? []).map((c) => (
              <div key={c.id} className="bg-gray-50 rounded p-2 text-sm">
                <span className="font-medium text-gray-700">{c.autor_nombre}</span>
                <span className="text-gray-400 text-xs ml-2">{new Date(c.created_at).toLocaleString()}</span>
                <p className="text-gray-600 mt-1">{c.texto}</p>
              </div>
            ))}
            {comentarios?.length === 0 && (
              <p className="text-xs text-gray-400">Sin comentarios.</p>
            )}
          </div>

          <div className="flex gap-2">
            <textarea
              value={nuevoComentario}
              onChange={(e) => setNuevoComentario(e.target.value)}
              placeholder="Nuevo comentario…"
              className={`${INPUT_CLASS} min-h-[60px]`}
            />
            <Button
              variant="primary"
              onClick={handleAgregarComentario}
              disabled={agregarCom.isPending || !nuevoComentario.trim()}
            >
              Enviar
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
