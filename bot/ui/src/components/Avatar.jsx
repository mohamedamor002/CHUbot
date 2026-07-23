import logo from '../assets/chulogo.png'

export default function Avatar({ onClick, connecting }) {
  return (
    <div
      data-tauri-drag-region
      className="w-20 h-20 flex items-center justify-center cursor-move select-none"
    >
      <button
        onClick={onClick}
        disabled={connecting}
        className={`
          w-16 h-16 rounded-full
          bg-white
          shadow-2xl
          flex items-center justify-center
          transition-all duration-200
          border border-slate-200
          overflow-hidden
          ${connecting
            ? 'opacity-60 cursor-wait'
            : 'hover:shadow-blue-500/40 hover:scale-110 active:scale-95 cursor-pointer'
          }
        `}
        title={connecting ? 'Démarrage du serveur...' : 'Ouvrir CHUbot'}
      >
        <img src={logo} alt="CHUbot" className="w-full h-full object-contain p-1" />
      </button>

      {connecting
        ? <span className="absolute w-16 h-16 rounded-full border-2 border-orange-400/60 animate-spin pointer-events-none" style={{ borderTopColor: 'transparent' }} />
        : <span className="absolute w-16 h-16 rounded-full border-2 border-blue-400/30 animate-ping pointer-events-none" />
      }
    </div>
  )
}
