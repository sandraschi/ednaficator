import React, { useEffect, useState } from 'react';
import { useEdnaStore, type LLMProvider } from '../../store';
import { Settings as SettingsIcon, X } from 'lucide-react';

const API = '/api';

export const SettingsModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const settings = useEdnaStore(s => s.settings);
  const setSettings = useEdnaStore(s => s.setSettings);

  const [provider, setProvider] = useState<LLMProvider>(settings.llm_provider);
  const [ollamaModel, setOllamaModel] = useState(settings.ollama_model);
  const [lmstudioModel, setLmstudioModel] = useState(settings.lmstudio_model);
  const [ollamaUrl, setOllamaUrl] = useState(settings.ollama_base_url);
  const [lmstudioUrl, setLmstudioUrl] = useState(settings.lmstudio_base_url);
  const [models, setModels] = useState<string[]>(settings.available_models);
  const [providerStatus, setProviderStatus] = useState<{
    ollama?: { available: boolean };
    lmstudio?: { available: boolean };
  }>({});

  const activeModel = provider === 'lmstudio' ? lmstudioModel : ollamaModel;

  useEffect(() => {
    if (!isOpen) return;

    fetch(`${API}/settings`)
      .then(res => res.json())
      .then(data => {
        setProvider(data.llm_provider ?? 'lmstudio');
        setOllamaModel(data.ollama_model ?? '');
        setLmstudioModel(data.lmstudio_model ?? '');
        setOllamaUrl(data.ollama_base_url ?? 'http://localhost:11434');
        setLmstudioUrl(data.lmstudio_base_url ?? 'http://127.0.0.1:1234/v1');
        setSettings({
          llm_provider: data.llm_provider,
          ollama_model: data.ollama_model,
          lmstudio_model: data.lmstudio_model,
          ollama_base_url: data.ollama_base_url,
          lmstudio_base_url: data.lmstudio_base_url,
        });
      })
      .catch(err => console.error('Failed to fetch settings:', err));

    fetch(`${API}/providers`)
      .then(res => res.json())
      .then(data => setProviderStatus(data))
      .catch(() => {});

    fetch(`${API}/models`)
      .then(res => res.json())
      .then(data => setModels(data.models ?? []))
      .catch(err => console.error('Failed to fetch models:', err));
  }, [isOpen, setSettings]);

  const handleProviderChange = async (next: LLMProvider) => {
    setProvider(next);
    try {
      await fetch(`${API}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ llm_provider: next }),
      });
      const res = await fetch(`${API}/models`);
      const data = await res.json();
      setModels(data.models ?? []);
      setSettings({ llm_provider: next, available_models: data.models ?? [] });
    } catch (err) {
      console.error('Provider switch failed:', err);
    }
  };

  const handleSave = async () => {
    try {
      const body: Record<string, string> = {
        llm_provider: provider,
        ollama_base_url: ollamaUrl,
        ollama_model: ollamaModel,
        lmstudio_base_url: lmstudioUrl,
        lmstudio_model: lmstudioModel,
      };
      const resp = await fetch(`${API}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      if (data.success) {
        setSettings({
          llm_provider: provider,
          ollama_model: ollamaModel,
          lmstudio_model: lmstudioModel,
          ollama_base_url: ollamaUrl,
          lmstudio_base_url: lmstudioUrl,
          available_models: models,
        });
        onClose();
      }
    } catch (err) {
      console.error('Failed to save settings:', err);
    }
  };

  if (!isOpen) return null;

  const ollamaUp = providerStatus.ollama?.available;
  const lmstudioUp = providerStatus.lmstudio?.available;

  return (
    <div className="modal-overlay">
      <div className="modal-content glass">
        <div className="modal-header">
          <div className="modal-title">
            <SettingsIcon size={18} />
            <span>Einstellungen</span>
          </div>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="modal-body">
          <div className="setting-group">
            <label>LLM Provider</label>
            <select
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value as LLMProvider)}
              className="glass-input"
            >
              <option value="lmstudio">
                LM Studio {lmstudioUp ? '(online)' : '(offline)'}
              </option>
              <option value="ollama">
                Ollama {ollamaUp ? '(online)' : '(offline)'}
              </option>
            </select>
            <p className="setting-hint">
              LM Studio: load a model in the app, enable the local server (port 1234).
              Ollama hängt oft beim Laden — LM Studio ist der Standard.
            </p>
          </div>

          {provider === 'lmstudio' ? (
            <>
              <div className="setting-group">
                <label>LM Studio URL</label>
                <input
                  type="text"
                  className="glass-input"
                  value={lmstudioUrl}
                  onChange={(e) => setLmstudioUrl(e.target.value)}
                />
              </div>
              <div className="setting-group">
                <label>Modell</label>
                <select
                  value={lmstudioModel}
                  onChange={(e) => setLmstudioModel(e.target.value)}
                  className="glass-input"
                >
                  <option value="">(auto — erstes geladenes Modell)</option>
                  {models.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                  {lmstudioModel && !models.includes(lmstudioModel) && (
                    <option value={lmstudioModel}>{lmstudioModel} (current)</option>
                  )}
                </select>
              </div>
            </>
          ) : (
            <>
              <div className="setting-group">
                <label>Ollama URL</label>
                <input
                  type="text"
                  className="glass-input"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                />
              </div>
              <div className="setting-group">
                <label>Ollama Modell</label>
                <select
                  value={ollamaModel}
                  onChange={(e) => setOllamaModel(e.target.value)}
                  className="glass-input"
                >
                  {models.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                  {ollamaModel && !models.includes(ollamaModel) && (
                    <option value={ollamaModel}>{ollamaModel} (current)</option>
                  )}
                </select>
              </div>
            </>
          )}

          <div className="setting-group">
            <label>Aktiv</label>
            <p className="setting-hint">{provider} → {activeModel || '(auto)'}</p>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Abbrechen</button>
          <button className="btn-primary" onClick={handleSave}>Speichern</button>
        </div>
      </div>
    </div>
  );
};
