import { useEffect, useRef, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faBuildingColumns, faSpinner } from '@fortawesome/free-solid-svg-icons'

/**
 * Autocompletado de universidades usando la API pública gratuita
 * de HipoLabs (http://universities.hipolabs.com). Si no hay conexión
 * o no hay resultados, el campo funciona como texto libre.
 */
export default function UniversityAutocomplete({ value, onChange, required = false }) {
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const containerRef = useRef(null)
  const debounceRef = useRef(null)

  // Cerrar el desplegable al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    const query = value.trim()
    if (query.length < 3) {
      setSuggestions([])
      setOpen(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const resp = await fetch(
          `https://universities.hipolabs.com/search?name=${encodeURIComponent(query)}`,
        )
        const data = await resp.json()
        // Nombres únicos, máximo 8 sugerencias
        const names = [...new Set(data.map((u) => u.name))].slice(0, 8)
        setSuggestions(names)
        setOpen(names.length > 0)
      } catch {
        setSuggestions([])
        setOpen(false)
      } finally {
        setLoading(false)
      }
    }, 350)
    return () => clearTimeout(debounceRef.current)
  }, [value])

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
          <FontAwesomeIcon icon={loading ? faSpinner : faBuildingColumns} spin={loading} />
        </span>
        <input
          type="text"
          required={required}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          placeholder="Universidad (empieza a escribir…)"
          autoComplete="off"
          className="w-full rounded-lg border border-slate-300 pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ins-500"
        />
      </div>

      {open && (
        <ul className="absolute z-20 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-56 overflow-y-auto">
          {suggestions.map((name) => (
            <li key={name}>
              <button
                type="button"
                onClick={() => {
                  onChange(name)
                  setOpen(false)
                }}
                className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-ins-50 hover:text-ins-800 transition-colors flex items-center gap-2"
              >
                <FontAwesomeIcon icon={faBuildingColumns} className="text-ins-400 text-xs shrink-0" />
                <span className="truncate">{name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
