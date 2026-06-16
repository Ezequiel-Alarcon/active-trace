import MonitorSeguimiento from '../components/MonitorSeguimiento';

export default function MonitorPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold text-gray-800">Monitor de seguimiento</h1>
      <MonitorSeguimiento />
    </div>
  );
}
