import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faEyeSlash } from '@fortawesome/free-solid-svg-icons'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 px-4">
      <span className="w-16 h-16 rounded-2xl bg-oft-600 text-white flex items-center justify-center text-2xl shadow-lg">
        <FontAwesomeIcon icon={faEyeSlash} />
      </span>
      <h1 className="mt-4 text-2xl font-bold text-slate-900">Página no encontrada</h1>
      <p className="mt-2 text-slate-500">La ruta que buscas no existe en INSOFT.</p>
      <Link
        to="/"
        className="mt-6 bg-ins-600 hover:bg-ins-700 text-white text-sm font-medium rounded-lg px-5 py-2.5 transition-all shadow-md shadow-oft-200"
      >
        Volver al inicio
      </Link>
    </div>
  )
}
