# k.LAB service web UI architecture

## Purpose

Every Spring-based k.LAB service can serve the same public Vue 3 dashboard at its context root. For
example, the reasoner dashboard is available at `http://localhost:8091/reasoner/`. Existing REST
clients continue to use the JSON endpoints below that context path.

The dashboard is intentionally split into two layers:

- `klab.core.services` owns the Spring controller, configuration contract, Vue/Quasar shell,
  authentication client, generic status display, and generic capability display.
- Each concrete `*.server` module owns its title, dashboard panels, and full-page components. Both
  extension forms receive the same context and API client, so later interfaces can be developed
  without changing the shell.

## Request flow

The browser loads `index.html` through `KlabWebUiController`. The shell then requests:

| Endpoint | Authentication | Purpose |
| --- | --- | --- |
| `/` | Public | Vue single-page application |
| `/ui/<component-name>` | Public shell | Direct entry point for a compiled full-page component |
| `/public/ui/config` | Public | Header, logo, authentication settings, links, and panel manifest |
| `/public/status` | Public, identity-aware when a token is present | Lightweight operational telemetry |
| `/public/capabilities` | Public, identity-aware when a token is present | Service identity, transports, components, and permissions |

Status and capabilities are refreshed every ten seconds. A failed refresh keeps the previous data
visible and displays a retry action. This keeps the dashboard useful while a service is starting or
temporarily busy.

`WebUiConfiguration` is the server-to-client contract. `ServiceNetworkedInstance` builds the
defaults and calls `configureWebUi(WebUiConfiguration.Builder)`. A derived Spring service overrides
that hook to change branding or add ordered `DashboardPanel` and `FullPageComponent` records.
Full-page records are sorted by `order` and appear as links in the desktop header and compact mobile
header menu. Their stable `name` is also their path segment under `/ui/`.

Spring forwards both `/` and `/ui/<component-name>` to the same SPA. A small `<base>` bootstrap in
`index.html` restores the service context root before Vite assets or API requests are resolved. This
allows direct entry and browser refresh to work when the service is mounted below a context path
such as `/reasoner`.

After the Spring-service hook runs, `ServiceNetworkedInstance` asks the primary service's
`ComponentRegistry` for installed-component contributions. A `KlabComponent` can add manifest
entries and map their component IDs to prebuilt ESM resources under `META-INF/klab/webui/` in its
archive. The generated public URL includes component ID and version; the controller serves only
explicitly declared modules from that component's PF4J classloader.

## Frontend layout

The frontend source is in `klab.core.services/src/main/webui`:

- `src/App.vue` coordinates configuration, authentication, polling, and panel composition.
- `src/services/api.ts` is the sole generic HTTP boundary. It refreshes the Keycloak token and adds
  `Authorization: Bearer <token>` when an identity exists.
- `src/services/auth.ts` owns the Keycloak adapter. Tokens remain in memory; they are never copied to
  local or session storage.
- `src/components/StatusGrid.vue` and `CapabilitiesPanel.vue` are the common public dashboard.
- `src/components/ExtensionPanel.vue` enforces the `requiresAuthentication` presentation rule and
  renders the configured component.
- `src/components/FullPageExtension.vue` renders the selected `/ui/` component and prevents a
  protected component from mounting until authentication succeeds.
- `src/components/AuthenticationDialog.vue` automatically presents the in-page sign-in gate for a
  protected direct-entry route.
- `vite.config.ts` discovers service components and creates the component registry at build time.
- `src/services/extensions.ts` resolves build-time components and lazily imports an explicit
  installed-component module when the public configuration supplies one.
- `src/plugin-api.ts` is emitted at the stable `assets/klab-webui-api.js` URL. An import map exposes
  it as `vue` and `@klab/webui`, ensuring installed modules share the shell's Vue runtime.

Panels receive a `DashboardContext` prop with the current configuration, status, capabilities,
authentication state, shared API client, and `refresh()` callback. The TypeScript interface in
`src/types.ts` is the generic downstream component contract.

The authorization requirement on a panel or page controls its presentation only. Server endpoints
remain the authority for access control. A component must never treat the manifest or a decoded
browser token as authorization.

## Keycloak integration

The public configuration contains only the values safe for a browser-based OpenID Connect client:
the Keycloak base URL, realm, and public client ID. There is no client secret in the application.
The compact header control starts the normal Keycloak authorization-code flow with PKCE; Keycloak
owns username/password collection. The initial dashboard remains anonymous by using `check-sso`
instead of `login-required`.

When a user enters an authentication-required `/ui/<name>` route directly, the shell completes
`check-sso` before mounting the component. If no session exists, it leaves the requested page in
place and opens a persistent Quasar dialog. Starting sign-in uses the Keycloak authorization-code
flow and sets the exact current route as `redirectUri`, so the identity provider returns the user
to the same component. Credentials are never collected by, or exposed to, the service UI.

Configure the server settings with Spring properties (for example in `application.properties` or
environment-backed configuration):

```properties
klab.webui.keycloak.url=https://identity.example.org
klab.webui.keycloak.realm=im
klab.webui.keycloak.client-id=klab-dashboard
```

Spring's equivalent environment variables are `KLAB_WEBUI_KEYCLOAK_URL`,
`KLAB_WEBUI_KEYCLOAK_REALM`, and `KLAB_WEBUI_KEYCLOAK_CLIENT_ID`.

If `klab.webui.keycloak.url` is absent, the dashboard stays public and shows no sign-in action. The
Keycloak client must be public, use authorization code + PKCE, allow the exact service dashboard
redirect URIs, and allow the service origin as a web origin.

The service authorization filter accepts both the historical raw JWT header and the standard
`Bearer` form produced by browser clients.

## Build and packaging

The normal Java build remains independent of Node.js. The `webui` Maven profile installs its pinned
Node/npm toolchain, performs a reproducible `npm ci`, type-checks the Vue sources, and runs the Vite
production build.

Compile the dashboard alone:

```bash
./mvnw -pl klab.core.services -Pwebui generate-resources
```

Package the generated files in `klab.core.services`:

```bash
./mvnw -pl klab.core.services -am -Pwebui package
```

Vite writes into `target/generated-resources/webui/static`. The Maven profile adds the parent
directory as a resource root, yielding Spring Boot's expected `classpath:/static/index.html` and
`classpath:/static/assets/*` layout.

Dependency versions are exact in `package.json` and `package-lock.json`. This avoids a dashboard
changing when a Java-only service build is repeated.

## Security boundaries

- The SPA, `/ui/**` shell routes, assets, configuration, status, health, and public capabilities
  remain anonymous so the client can present the authentication dialog.
- A token is attached automatically when present, allowing capabilities and downstream components
  to receive identity-specific responses.
- Protected REST endpoints remain covered by `ServiceSecurityConfiguration` and the existing k.LAB
  role/permission checks.
- The panel manifest contains presentation metadata, never secrets or authorization decisions.
- Remote component URLs are not executed. Build-time extensions are compiled into the service;
  runtime extensions must come from trusted, installed k.LAB component archives and are served from
  the service origin. Arbitrary URLs in component metadata are never exposed to the browser.
