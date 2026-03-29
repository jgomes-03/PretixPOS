import type { BetterPOSConfig } from './types';

declare global {
  interface Window {
    BETTERPOS?: Partial<BetterPOSConfig>;
  }
}

function isMissing(v: unknown): boolean {
  return (
    v === undefined ||
    v === null ||
    v === '' ||
    v === 'undefined' ||
    v === 'None' ||
    v === 'null'
  );
}

function parseEventContextFromPath(pathname: string): { organizer: string; event: string } | null {
  const m = pathname.match(/^\/control\/event\/([^/]+)\/([^/]+)\//);
  if (!m) {
    return null;
  }
  return { organizer: m[1], event: m[2] };
}

function asBool(v: unknown): boolean {
  return v === true || v === 'true' || v === '1' || v === 1;
}

export function getMountNode(): HTMLElement | null {
  return document.getElementById('betterpos-app');
}

export function normalizeConfig(): BetterPOSConfig {
  const mountNode = getMountNode();
  const ds = (mountNode?.dataset ?? {}) as DOMStringMap;
  const cfg: Partial<BetterPOSConfig> = window.BETTERPOS || {};

  if (isMissing(cfg.organizer) && !isMissing(ds.organizer)) cfg.organizer = ds.organizer;
  if (isMissing(cfg.event) && !isMissing(ds.event)) cfg.event = ds.event;
  if (isMissing(cfg.basePath) && !isMissing(ds.basePath)) cfg.basePath = ds.basePath;
  if (isMissing(cfg.apiBase) && !isMissing(ds.apiBase)) cfg.apiBase = ds.apiBase;
  if (isMissing(cfg.csrfToken) && !isMissing(ds.csrfToken)) cfg.csrfToken = ds.csrfToken;

  const parsed = parseEventContextFromPath(window.location.pathname);
  if (parsed) {
    if (isMissing(cfg.organizer)) cfg.organizer = parsed.organizer;
    if (isMissing(cfg.event)) cfg.event = parsed.event;
    if (isMissing(cfg.basePath)) {
      cfg.basePath = `/control/event/${parsed.organizer}/${parsed.event}/betterpos`;
    }
  }

  if (isMissing(cfg.apiBase) && !isMissing(cfg.basePath)) {
    cfg.apiBase = `${String(cfg.basePath).replace(/\/$/, '')}/api`;
  }

  if (!cfg.permissions || typeof cfg.permissions !== 'object') {
    cfg.permissions = {
      canManageRegisters: asBool(ds.canManageRegisters),
      canViewAudit: asBool(ds.canViewAudit),
      canSessionControl: asBool(ds.canSessionControl),
      canSell: asBool(ds.canSell),
    };
  }

  return {
    organizer: String(cfg.organizer || ''),
    event: String(cfg.event || ''),
    basePath: String(cfg.basePath || ''),
    apiBase: String(cfg.apiBase || ''),
    csrfToken: isMissing(cfg.csrfToken) ? undefined : String(cfg.csrfToken),
    permissions: {
      canManageRegisters: asBool(cfg.permissions.canManageRegisters),
      canViewAudit: asBool(cfg.permissions.canViewAudit),
      canSessionControl: asBool(cfg.permissions.canSessionControl),
      canSell: asBool(cfg.permissions.canSell),
    },
  };
}
