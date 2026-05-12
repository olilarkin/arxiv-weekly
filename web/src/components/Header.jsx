export default function Header({ total, loading }) {
  return (
    <div style={{ borderBottom: '1px solid #1e293b', background: '#0a0d14',
      padding: 'clamp(12px,3vw,18px) clamp(12px,4vw,26px) 14px' }}>
      <div style={{ fontSize: 10, color: '#38bdf8', letterSpacing: 4, opacity: 0.7, marginBottom: 6 }}>
        ARXIV MONITOR / CS.SD - EESS.AS
      </div>
      <div style={{ fontFamily: "'Space Mono',monospace", fontWeight: 700,
        color: '#f1f5f9', letterSpacing: -0.5, lineHeight: 1.4,
        fontSize: 'clamp(15px,4vw,21px)' }}>
        Audio AI Weekly
        <span style={{ fontSize: 'clamp(10px,2.5vw,12px)', color: '#475569',
          fontWeight: 400, marginLeft: 10 }}>
          Audio Foundation Models · Source Separation · Music Transcription & Beat Tracking
        </span>
      </div>
      {!loading && total > 0 && (
        <div style={{ fontSize: 10, color: '#475569', marginTop: 4 }}>
          Showing {total} papers
        </div>
      )}
    </div>
  )
}
