import React, { useEffect, useRef, useCallback } from 'react';
import { useEdnaStore } from '../../store';
import { useEdnaWS } from '../../hooks/useEdnaWS';
import { MessageBubble, ThinkingDot } from './MessageBubble';
import { InputBar } from './InputBar';
import { EmptyState } from './EmptyState';

export const ChatContainer: React.FC = () => {
  const { send }      = useEdnaWS();
  const messages      = useEdnaStore(s => s.messages);
  const thinking      = useEdnaStore(s => s.thinking);
  const addMessage    = useEdnaStore(s => s.addMessage);
  const bottomRef     = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  const handleSend = useCallback((text: string) => {
    addMessage({ role: 'user', content: text, timestamp: new Date().toISOString() });
    send(text);
  }, [addMessage, send]);

  return (
    <section className="chat">
      <div className="chat__msgs">
        {messages.length === 0 && <EmptyState onSend={handleSend} />}
        {messages.map(m => <MessageBubble key={m.id} msg={m} />)}
        {thinking && <ThinkingDot />}
        <div ref={bottomRef} />
      </div>
      <InputBar onSend={handleSend} />
    </section>
  );
};
