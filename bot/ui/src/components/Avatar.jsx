export default function Avatar({ onClick }) {
  return (
    // Zone draggable (le pourtour du cercle)
    <div
      data-tauri-drag-region
      className="w-20 h-20 flex items-center justify-center cursor-move select-none"
    >
      {/* Bouton central — click only, pas de drag */}
      <button
        onClick={onClick}
        className="
          w-16 h-16 rounded-full
          bg-gradient-to-br from-blue-600 to-blue-800
          shadow-2xl hover:shadow-blue-500/50
          flex flex-col items-center justify-center gap-0.5
          hover:scale-110 active:scale-95
          transition-all duration-200
          border-2 border-white/20
          cursor-pointer
        "
        title="Ouvrir CHUbot"
      >
        {/* Croix médicale */}
        <svg width="22" height="22" viewBox="0 0 24 24" fill="white">
          <rect x="10" y="3" width="4" height="18" rx="1" />
          <rect x="3" y="10" width="18" height="4" rx="1" />
        </svg>
        <span className="text-white text-[9px] font-bold tracking-widest leading-none">
          CHU
        </span>
      </button>

      {/* Anneau de pulsation */}
      <span className="absolute w-16 h-16 rounded-full border-2 border-blue-400/40 animate-ping pointer-events-none" />
    </div>
  )
}
