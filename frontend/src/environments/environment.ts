export const environment = {
  production: false,
  // A tenant subdomain must reach the backend on that SAME subdomain (e.g.
  // kem-school.localtest.me:8000, not plain localhost:8000) - the backend
  // resolves which tenant a request belongs to from the Host header, and a
  // fixed cross-origin target would always send "localhost:8000" regardless
  // of which subdomain the app itself is running on. Evaluated once at
  // module load, which happens after window.location is available and
  // before any per-domain service builds its BASE_URL from this.
  get apiUrl(): string {
    return `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;
  },
  primeNgLicenseKey:
    'eyJpZCI6ImJlOTY3YmMwLTJmMWQtNDZmYS1hNmUwLTBkZDhmMGE3YjdjYSIsInByb2R1Y3QiOiJwcmltZXVpIiwidGllciI6ImNvbW11bml0eSIsInR5cGUiOiJkZXYiLCJpYXQiOjE3ODU5OTgzOTAsImV4cCI6MTgxNzUzNDM5MH0.Ms4C-a1ApOvuXg8a7spjcgg0ZG2DenTP0p_LQMk3c9V6YqyylaOu6s-ddYzBSIb4n-1VdmB3N-jI1pOz6mXNDg',
};
