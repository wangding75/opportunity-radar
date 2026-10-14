export interface ApiFieldError {
  field: string;
  message: string;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  fieldErrors: ApiFieldError[];
  requestId?: string;
  retryable: boolean;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly payload: ApiErrorPayload,
  ) {
    super(payload.message);
    this.name = 'ApiError';
  }
}

export interface RequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  body?: BodyInit | Record<string, unknown>;
  headers?: HeadersInit;
  requestId?: string;
}

let csrfCookieName = 'or_csrf';

export function configureApiClient(options: { csrfCookieName?: string }): void {
  csrfCookieName = options.csrfCookieName || 'or_csrf';
}

function readCookie(name: string): string | undefined {
  const target = `${encodeURIComponent(name)}=`;
  return document.cookie.split(';').map(part => part.trim()).find(part => part.startsWith(target))?.slice(target.length);
}

function isWriteMethod(method: string): boolean {
  return !['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase());
}

function toRequestBody(body: RequestOptions['body']): BodyInit | undefined {
  if (!body || body instanceof FormData || body instanceof URLSearchParams || typeof body === 'string' || body instanceof Blob) return body;
  return JSON.stringify(body);
}

function errorPayload(status: number, body: unknown, requestId?: string): ApiErrorPayload {
  const value = body && typeof body === 'object' ? body as Record<string, unknown> : {};
  const detail = value.detail;
  const message = typeof value.message === 'string'
    ? value.message
    : typeof detail === 'string'
      ? detail
      : `请求失败（HTTP ${status}）`;
  const fieldErrors = Array.isArray(value.field_errors)
    ? value.field_errors.filter((item): item is ApiFieldError => Boolean(item && typeof item === 'object' && typeof (item as ApiFieldError).field === 'string' && typeof (item as ApiFieldError).message === 'string'))
    : [];
  return {
    code: typeof value.code === 'string' ? value.code : `HTTP_${status}`,
    message,
    fieldErrors,
    requestId,
    retryable: status === 429 || status >= 500,
  };
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method || 'GET';
  const body = toRequestBody(options.body);
  const headers = new Headers(options.headers);
  const requestId = options.requestId || crypto.randomUUID();
  headers.set('X-Request-ID', requestId);
  if (body && !(body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (isWriteMethod(method)) {
    const csrf = readCookie(csrfCookieName);
    if (csrf) headers.set('X-CSRF-Token', decodeURIComponent(csrf));
  }

  let response: Response;
  try {
    response = await fetch(path, { ...options, method, body, headers, credentials: 'same-origin' });
  } catch {
    throw new ApiError(0, {
      code: 'NETWORK_ERROR',
      message: '网络不可用，请检查连接后重试。',
      fieldErrors: [],
      requestId,
      retryable: true,
    });
  }

  const responseRequestId = response.headers.get('X-Request-ID') || requestId;
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json().catch(() => undefined) : undefined;
  if (!response.ok) throw new ApiError(response.status, errorPayload(response.status, payload, responseRequestId));
  return payload as T;
}

export async function download(path: string, filename: string, signal?: AbortSignal): Promise<void> {
  const response = await fetch(path, { credentials: 'same-origin', signal });
  if (!response.ok) throw new ApiError(response.status, errorPayload(response.status, await response.json().catch(() => undefined), response.headers.get('X-Request-ID') || undefined));
  const href = URL.createObjectURL(await response.blob());
  try {
    const anchor = document.createElement('a');
    anchor.href = href;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(href);
  }
}
