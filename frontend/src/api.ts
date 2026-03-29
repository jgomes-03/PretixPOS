import type {
  AuditRow,
  BetterPOSConfig,
  CatalogItem,
  Register,
  ReportSummary,
  Session,
  Transaction,
} from './types';

function getCookie(name: string): string | null {
  let cookieValue: string | null = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i += 1) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function normalizeToken(value?: string | null): string | null {
  if (!value) return null;
  const token = String(value).trim();
  if (!token || token === 'NOTPROVIDED' || token === 'undefined' || token === 'None' || token === 'null') {
    return null;
  }
  return token;
}

function getMetaCsrfToken(): string | null {
  const meta = document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement | null;
  return normalizeToken(meta?.content || null);
}

function getInputCsrfToken(): string | null {
  const input = document.querySelector('input[name="csrfmiddlewaretoken"]') as HTMLInputElement | null;
  return normalizeToken(input?.value || null);
}

function getCsrfToken(preferred?: string): string | null {
  return (
    normalizeToken(preferred) ||
    getMetaCsrfToken() ||
    getInputCsrfToken() ||
    normalizeToken(getCookie('csrftoken'))
  );
}

async function jsonFetch<T>(url: string, options?: RequestInit, csrfHint?: string): Promise<T> {
  const opts: RequestInit = { ...(options || {}) };
  const method = (opts.method || 'GET').toUpperCase();
  opts.credentials = 'same-origin';
  opts.headers = {
    'Content-Type': 'application/json',
    ...(opts.headers || {}),
  };

  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const csrfToken = getCsrfToken(csrfHint);
    if (csrfToken) {
      (opts.headers as Record<string, string>)['X-CSRFToken'] = csrfToken;
    }
  }

  const res = await fetch(url, opts);
  const raw = await res.text();
  let data: unknown = {};

  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = { error: raw || 'Invalid response' };
  }

  if (!res.ok) {
    const error = (data as { error?: string }).error || `HTTP ${res.status}`;
    throw new Error(error);
  }

  return data as T;
}

export function createApi(config: BetterPOSConfig) {
  const csrfHint = config.csrfToken;

  return {
    registersList: () => jsonFetch<{ registers: Register[] }>(`${config.apiBase}/registers/`, undefined, csrfHint),
    registerCreate: (payload: { name: string; code: string; currency: string }) =>
      jsonFetch<Register>(`${config.apiBase}/registers/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }, csrfHint),
    registerUpdate: (id: number, payload: Partial<Register>) =>
      jsonFetch<Register>(`${config.apiBase}/registers/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }, csrfHint),
    registerDelete: (id: number) =>
      jsonFetch<{ ok: boolean }>(`${config.apiBase}/registers/${id}/`, {
        method: 'DELETE',
      }, csrfHint),
    sessionStatus: (registerId: number) =>
      jsonFetch<{ has_open_session: boolean; register_id?: number; session?: Session }>(
        `${config.apiBase}/session/status/?register_id=${registerId}`,
        undefined,
        csrfHint
      ),
    sessionOpen: (payload: { register_id: number; opening_float: string }) =>
      jsonFetch<{ session_id: number; status: string }>(`${config.apiBase}/session/open/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }, csrfHint),
    sessionClose: (payload: { register_id: number; counted_cash: string }) =>
      jsonFetch<{ session_id: number; status: string }>(`${config.apiBase}/session/close/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }, csrfHint),
    sessionsList: () => jsonFetch<{ sessions: Session[] }>(`${config.apiBase}/sessions/?limit=100`, undefined, csrfHint),
    catalog: () => jsonFetch<{ items: CatalogItem[] }>(`${config.apiBase}/catalog/`, undefined, csrfHint),
    orderCreate: (payload: {
      register_id: number;
      lines: Array<{ item_id: number; quantity: number }>;
      idempotency_key?: string;
    }) =>
      jsonFetch<{ order_code: string; transaction: Transaction }>(`${config.apiBase}/order/create/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }, csrfHint),
    payCash: (payload: { transaction_id: number }) =>
      jsonFetch<{ payment_id: number; transaction: Transaction }>(`${config.apiBase}/payment/cash/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }, csrfHint),
    payEupago: (payload: { transaction_id: number; provider?: string; phone?: string }) =>
      jsonFetch<{ payment_id: number; transaction: Transaction; provider_response: string }>(
        `${config.apiBase}/payment/eupago/`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        },
        csrfHint
      ),
    transactionStatus: (transactionId: number) =>
      jsonFetch<{ transaction: Transaction }>(`${config.apiBase}/transaction/${transactionId}/status/`, undefined, csrfHint),
    transactionsList: () =>
      jsonFetch<{ transactions: Transaction[] }>(`${config.apiBase}/transactions/?limit=200`, undefined, csrfHint),
    auditFeed: () => jsonFetch<{ actions: AuditRow[] }>(`${config.apiBase}/audit/feed/?limit=200`, undefined, csrfHint),
    reportsSummary: (days: number) =>
      jsonFetch<ReportSummary>(`${config.apiBase}/reports/summary/?days=${days}`, undefined, csrfHint),
  };
}
