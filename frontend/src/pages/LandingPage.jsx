import { motion, useReducedMotion } from 'motion/react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faChevronDown } from '@fortawesome/free-solid-svg-icons'
import { Link } from 'react-router-dom'
import Logo from '../components/Logo'

const EASE = [0.16, 1, 0.3, 1]

export default function LandingPage() {
  const reduce = useReducedMotion()

  const heroStagger = reduce
    ? {}
    : {
        initial: 'hidden',
        animate: 'show',
        variants: { show: { transition: { staggerChildren: 0.09 } } },
      }
  const heroItem = reduce
    ? {}
    : {
        variants: {
          hidden: { opacity: 0, y: 20 },
          show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } },
        },
      }

  return (
    <main className="relative flex h-screen snap-start flex-col overflow-hidden bg-slate-950 font-sans text-white antialiased">
      <video
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        aria-hidden="true"
        className="absolute inset-0 h-full w-full object-cover"
      >
        <source src="/videos/Modern_hospital_room_interior_202609061543.mp4" type="video/mp4" />
      </video>
      <div className="absolute inset-0 bg-slate-950/60" />
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/70 via-transparent to-slate-950/85" />

      <header className="relative z-10">
        <div className="h-1 w-full bg-ins-600" />
        <div className="flex h-16 items-center justify-between px-6 lg:px-12">
          <Logo size="text-2xl" light />
          <Link
            to="/login"
            className="rounded-lg bg-ins-700 px-5 py-2 text-sm font-semibold text-white shadow-ins-sm transition-colors hover:bg-ins-800"
          >
            Acceder
          </Link>
        </div>
      </header>

      <div className="relative z-10 flex flex-1 items-center justify-center px-6 py-10 text-center">
        <motion.div {...heroStagger} className="mx-auto max-w-3xl">
          <motion.p
            {...heroItem}
            className="text-sm font-semibold uppercase tracking-[0.16em] text-ins-300"
          >
            Plataforma de aprendizaje de Oftalmología
          </motion.p>
          <motion.h1
            {...heroItem}
            className="mt-4 text-4xl font-extrabold leading-[1.08] tracking-tight text-white md:text-5xl lg:text-6xl"
          >
            Aprende <span className="text-ins-300">Oftalmología</span> con el contenido oficial
          </motion.h1>
          <motion.p
            {...heroItem}
            className="mx-auto mt-5 max-w-[52ch] text-lg leading-relaxed text-slate-200"
          >
            Estudia temas verificados, únete a los cursos de tu facultad con un código y sigue tu
            progreso en cada subtema.
          </motion.p>
          <motion.div {...heroItem} className="mt-8">
            <motion.div whileHover={reduce ? undefined : { y: -2 }} whileTap={reduce ? undefined : { scale: 0.98 }}>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 rounded-xl bg-ins-700 px-7 py-3.5 text-base font-semibold text-white shadow-ins-md transition-colors hover:bg-ins-800"
              >
                Acceder
                <FontAwesomeIcon icon={faArrowRight} />
              </Link>
            </motion.div>
          </motion.div>

          <motion.div
            {...heroItem}
            className="mx-auto mt-10 flex max-w-fit items-center justify-center gap-4 border-t border-white/15 pt-6"
          >
            <span className="text-4xl font-extrabold tracking-tight text-white">14</span>
            <span className="max-w-[22ch] text-left text-sm leading-tight text-slate-300">
              subtemas del temario oficial de Oftalmología, disponibles desde el primer día
            </span>
          </motion.div>
        </motion.div>
      </div>

      <motion.div
        className="relative z-10 pb-6 text-center"
        animate={reduce ? undefined : { y: [0, 8, 0] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
      >
        <FontAwesomeIcon icon={faChevronDown} className="text-lg text-white/60" aria-hidden="true" />
      </motion.div>
    </main>
  )
}
