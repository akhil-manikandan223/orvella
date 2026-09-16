import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

// Defense-in-depth against the browser's back/forward cache (bfcache):
// on back/forward navigation, browsers can restore an entire previous page
// - DOM and JS state included - from a frozen snapshot, without ever
// re-running Angular's router or its auth guards. That would silently show
// an authenticated page again even after the user has since logged out.
// The Cache-Control header on the served HTML (see app/main.py) is the
// primary defense; this is a belt-and-braces fallback for any browser/dev
// setup where that header isn't honored - a persisted pageshow event means
// the page came from bfcache, so force a real reload to go through the
// guards again.
window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    window.location.reload();
  }
});

bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));
