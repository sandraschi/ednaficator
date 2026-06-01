import React, { useRef, useState, KeyboardEvent, useCallback } from 'react';
import { useEdnaStore } from '../../store';
import { OrnamentH } from '../common/Ornament';
import { SendHorizontal } from 'lucide-react';

export const InputBar: React.FC<{ onSend: (m: string) => void }> = ({ onSend }) => {
  const [val, setVal] = useState('');
  const thinking = useEdnaStore(s => s.thinking);
  const ref = useRef<HTMLTextAreaElement>(null);

  const submit = useCallback(() => {
    const t = val.trim();
    if (!t || thinking) return;
    onSend(t);
    setVal('');
    ref.current?.focus();
  }, [val, thinking, onSend]);

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <div className="inputbar glass">
      <OrnamentH />
      <div className="inputbar__inner">
        <textarea
          ref={ref}
          className="inputbar__ta"
          rows={1}
          placeholder="Sag mir was… (Enter zum Senden)"
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={onKey}
          disabled={thinking}
          autoFocus
        />
        <button className="inputbar__btn" onClick={submit} disabled={thinking || !val.trim()}>
          {thinking ? '…' : <SendHorizontal size={18} />}
        </button>
      </div>
    </div>
  );
};
