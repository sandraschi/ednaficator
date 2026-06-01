import React from 'react';
import { Message } from '../../store';

interface MsgBubbleProps {
  msg: Message;
}

export const MessageBubble: React.FC<MsgBubbleProps> = ({ msg }) => {
  const ts = msg.timestamp
    ? new Date(msg.timestamp).toLocaleTimeString('de-AT', { hour: '2-digit', minute: '2-digit' })
    : '';

  if (msg.role === 'system') {
    return <div className="msg__system">{msg.content}</div>;
  }

  return (
    <div className={`msg msg--${msg.role} glass`}>
      <div className="msg__meta">
        <span className="msg__who">
          {msg.role === 'user' ? 'you' : msg.role === 'error' ? 'err' : 'edna'}
        </span>
        <span className="msg__ts">{ts}</span>
      </div>
      <div className="msg__body">{msg.content}</div>
      {msg.toolCall && (
        <div className="msg__tool">
          ▸ [{msg.toolCall.server}] {msg.toolCall.tool}
        </div>
      )}
      {msg.actions && msg.actions.length > 0 && (
        <div className="msg__actions">
          {msg.actions.map((a, i) => <span key={i} className="msg__action">{a}</span>)}
        </div>
      )}
    </div>
  );
};

export const ThinkingDot = () => (
  <div className="thinking-wrap">
    <span className="thinking-label">edna denkt nach</span>
    <span className="dot-pulse" />
    <span className="dot-pulse" style={{ animationDelay: '0.2s' }} />
    <span className="dot-pulse" style={{ animationDelay: '0.4s' }} />
  </div>
);
