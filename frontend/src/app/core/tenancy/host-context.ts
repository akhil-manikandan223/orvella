/**
 * Whether the app was loaded from a tenant subdomain (e.g.
 * kem-school.localtest.me) rather than the bare platform-admin origin
 * (localhost, or the bare base domain).
 *
 * This is a routing/UX convenience ONLY - it decides which set of routes
 * and which login flow to show. It carries no security weight: the backend
 * independently resolves and enforces the tenant from the Host header of
 * each API request (see app/api/deps.py get_current_tenant), so a user
 * can never see another tenant's data just because the frontend guessed
 * "tenant mode" one way or the other.
 */
export function isTenantHost(): boolean {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return false;
  }
  // A subdomain label present before the base domain, e.g.
  // "kem-school.localtest.me" (3 labels) vs the bare "localtest.me" or
  // "orvella.com" (2 labels) that the platform-admin console itself would
  // run on in production.
  return hostname.split('.').length >= 3;
}
