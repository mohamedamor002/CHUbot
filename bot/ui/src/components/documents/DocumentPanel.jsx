import { useState, useEffect, useRef } from 'react'
import { uploadDocument, listDocuments } from '../../api/client.js'

export default function DocumentPanel() {
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    fetchDocuments()
  }, [])

  async function fetchDocuments() {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch {
      // silently fail on list
    }
  }

  async function handleUpload(file) {
    if (!file) return
    const allowed = ['.pdf', '.docx', '.doc', '.xlsx', '.xls']
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      setError(`Format non supporte. Formats acceptes : ${allowed.join(', ')}`)
      return
    }

    setUploading(true)
    setProgress(0)
    setError(null)
    setSuccess(null)

    try {
      const result = await uploadDocument(file, setProgress)
      setSuccess(`"${result.filename}" indexe avec succes (${result.chunks_indexed} chunks)`)
      await fetchDocuments()
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement.')
    } finally {
      setUploading(false)
      setProgress(0)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-blue-200 uppercase tracking-wider">Documents RH</p>

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
          dragging ? 'border-blue-400 bg-blue-500/20' : 'border-white/20 hover:border-white/40 hover:bg-white/5'
        } ${uploading ? 'opacity-60 cursor-not-allowed' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.doc,.xlsx,.xls"
          className="hidden"
          onChange={(e) => handleUpload(e.target.files[0])}
          disabled={uploading}
        />
        <svg className="w-8 h-8 mx-auto text-blue-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        <p className="text-xs text-blue-200">
          {uploading ? 'Chargement...' : 'Glissez un fichier ou cliquez'}
        </p>
        <p className="text-xs text-blue-300/60 mt-1">PDF, Word, Excel — max 20 Mo</p>
      </div>

      {/* Progress bar */}
      {uploading && progress > 0 && (
        <div className="w-full bg-white/10 rounded-full h-1.5">
          <div
            className="bg-blue-400 h-1.5 rounded-full transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Feedback */}
      {error && (
        <p className="text-xs text-red-300 bg-red-500/10 rounded-lg px-3 py-2">{error}</p>
      )}
      {success && (
        <p className="text-xs text-green-300 bg-green-500/10 rounded-lg px-3 py-2">{success}</p>
      )}

      {/* Document list */}
      {documents.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs text-blue-300/70 uppercase tracking-wider mt-2">Indexes</p>
          {documents.map((doc, i) => (
            <div key={i} className="flex items-start gap-2 bg-white/5 rounded-lg px-3 py-2">
              <svg className="w-4 h-4 text-blue-300 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div className="min-w-0">
                <p className="text-xs text-white truncate">{doc.filename}</p>
                <p className="text-xs text-blue-300/60">{doc.chunks_indexed} chunks</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {documents.length === 0 && !uploading && (
        <p className="text-xs text-blue-300/50 text-center py-2">Aucun document indexe</p>
      )}
    </div>
  )
}
