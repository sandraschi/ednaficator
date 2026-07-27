import React from 'react';
import { useEdnaStore, ServerInfo } from '../../store';
import { OrnamentH } from '../common/Ornament';
import { Server as ServerIcon, ShieldCheck } from 'lucide-react';

const ServerRow = ({ s }: { s: ServerInfo }) => (
  <div className={`srv srv--${s.ready ? 'ok' : s.error ? 'err' : 'idle'}`}>
    <span className="srv__dot" />
    <span className="srv__name" title={s.error ?? ''}>{s.name}</span>
    {s.ready && <span className="srv__count">{s.tool_count}t</span>}
  </div>
);

export const Sidebar: React.FC<{ open: boolean }> = ({ open }) => {
  const servers = useEdnaStore(s => s.servers);
  const registry = useEdnaStore(s => s.mcpRegistry);
  const ready   = servers.filter(s => s.ready).length;
  const configLabel = registry?.config_path
    ? registry.config_path.split(/[/\\]/).pop()
    : 'Claude Desktop config';
  
  return (
    <aside className={`sidebar glass ${open ? 'sidebar--open' : 'sidebar--closed'}`}>
      <div className="sidebar__head">
        <div className="sidebar__title-wrap">
          <ServerIcon size={16} />
          <span className="sidebar__title">MCP Registry</span>
        </div>
        <span className="sidebar__count">{ready}/{servers.length}</span>
      </div>
      <div className="sidebar__meta">
        from {configLabel}
        {registry?.allowlist_active ? ' · allowlist' : ''}
      </div>
      <OrnamentH />
      <div className="sidebar__list">
        {servers.length === 0
          ? <div className="sidebar__empty">No servers in Claude config (or allowlist filtered all)</div>
          : servers.map(s => <ServerRow key={s.name} s={s} />)
        }
      </div>
      
      <div className="sidebar__footer">
        <div className="sidebar__security">
          <ShieldCheck size={14} className="text-gold" />
          <span>Local Processing Only</span>
        </div>
      </div>
    </aside>
  );
};
