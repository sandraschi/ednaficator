import React from 'react';
import { useEdnaStore } from '../../store';

export const EmptyState = ({ onSend }: { onSend: (t: string) => void }) => {
  const servers  = useEdnaStore(s => s.servers);
  const connected = useEdnaStore(s => s.connected);
  const settings = useEdnaStore(s => s.settings);
  const ready = servers.filter(s => s.ready).length;
  const total = servers.length;

  const EXAMPLES = [
    'Was läuft gerade in meinem Plex?',
    'Suche in Calibre nach Philip K. Dick',
    'Zeig mir meine letzten Git-Commits',
    'Wie ist das Wetter in Wien?',
  ];

  return (
    <div className="chat__empty">
      <div className="chat__empty-ornament">◆</div>
      <div className="chat__empty-title">Servus</div>
      <div className="chat__empty-sub">Lokale KI · Goliath · Wien 9</div>

      <div className="chat__empty-status glass">
        <span className={`chat__empty-dot ${connected ? 'on' : 'off'}`} />
        <span>{connected ? 'verbunden' : 'getrennt'}</span>
        <span className="chat__empty-sep">·</span>
        <span className="text-gold">
          {settings.llm_provider === 'lmstudio'
            ? (settings.lmstudio_model || 'lmstudio:auto')
            : settings.ollama_model}
        </span>
        <span className="chat__empty-sep">·</span>
        <span>{ready}/{total} MCP-Server</span>
      </div>

      {!connected && (
        <div className="chat__empty-warn glass">
          Backend nicht erreichbar — läuft <code>ednaficator-start.bat</code>?
        </div>
      )}

      {connected && ready === 0 && total > 0 && (
        <div className="chat__empty-warn glass">
          Keine MCP-Server aktiv — Edna antwortet nur als Chat.
        </div>
      )}

      <div className="chat__empty-examples">
        <div className="chat__empty-examples-label">Beispiele</div>
        <div className="chat__example-grid">
          {EXAMPLES.map(t => (
            <button key={t} className="chat__example glass-btn" onClick={() => onSend(t)}>
              {t}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
