import type { InboxThreadItem } from '../types/mensajes';

interface InboxListProps {
  threads: InboxThreadItem[];
  selectedHiloId: string | null;
  onSelect: (hiloId: string) => void;
}

export default function InboxList({ threads, selectedHiloId, onSelect }: InboxListProps) {
  if (threads.length === 0) {
    return <p className="text-sm text-gray-400 px-4 py-3">No hay mensajes.</p>;
  }

  return (
    <ul className="divide-y divide-gray-100">
      {threads.map((thread) => (
        <li key={thread.hilo_id}>
          <button
            type="button"
            onClick={() => onSelect(thread.hilo_id)}
            className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
              selectedHiloId === thread.hilo_id ? 'bg-blue-50 border-l-2 border-blue-600' : ''
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <span
                className={`text-sm truncate ${
                  thread.leido ? 'text-gray-600' : 'text-gray-900 font-semibold'
                }`}
              >
                {thread.ultimo_asunto}
              </span>
              {!thread.leido && (
                <span className="flex-shrink-0 h-2 w-2 rounded-full bg-blue-600 mt-1" />
              )}
            </div>
            <p className="text-xs text-gray-400 truncate mt-0.5">{thread.ultimo_cuerpo}</p>
            <p className="text-xs text-gray-300 mt-1">
              {new Date(thread.ultima_actividad).toLocaleString('es-AR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </button>
        </li>
      ))}
    </ul>
  );
}
