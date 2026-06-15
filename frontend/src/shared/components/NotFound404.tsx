import { Link } from 'react-router-dom';

export default function NotFound404() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4 text-center px-4">
      <h1 className="text-5xl font-bold text-gray-300">404</h1>
      <h2 className="text-xl font-semibold text-gray-700">Página no encontrada</h2>
      <p className="text-gray-500">La página que buscás no existe o fue movida.</p>
      <Link to="/" className="text-blue-600 hover:underline text-sm">
        Volver al inicio
      </Link>
    </div>
  );
}
