export interface ApiValidationDetail {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

export type ApiErrorCode =
  | 'validation_error'
  | 'http_error'
  | 'conflict'
  | 'invalid_reference'
  | 'internal_error';

export interface ApiError {
  error: {
    code: ApiErrorCode;
    message: string;
    details?: ApiValidationDetail[];
  };
}
