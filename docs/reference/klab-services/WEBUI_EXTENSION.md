# Extending the k.LAB service web UI

## Change a service dashboard

Override `configureWebUi` in the concrete `ServiceNetworkedInstance` subclass. The four server
modules contain examples.

```java
@Override
protected void configureWebUi(WebUiConfiguration.Builder dashboard) {
  dashboard
      .title("My k.LAB service")
      .subtitle("A concise description of the service")
      .logoUrl("my-service-logo.svg")
      .link("Documentation", "https://docs.example.org", true)
      .panel(
          "catalog",
          "Catalog",
          "Browse the objects advertised by this service.",
          "catalog-browser",
          100,
          true)
      .page(
          "catalog",
          "Resource catalog",
          "Browse and manage the resources advertised by this service.",
          "catalog-workspace",
          100,
          true);
}
```

Panel arguments are, in order: stable panel ID, heading, description, Vue component ID, sort order,
and whether the shell should require a signed-in user before mounting the component. IDs should be
lowercase kebab-case and remain stable across releases.

Full-page arguments follow the same pattern: stable URL name, title, description, Vue component ID,
sort order, and authentication requirement. The example is mounted at `/ui/catalog`. Registered
pages automatically become links in the dashboard header, ordered by `order`; no separate link
configuration is needed.

`logoUrl` is resolved relative to the service context root. Replace the core `klab-logo.svg` for a
global brand or package another static resource under the same Spring Boot static-resource rules
and point the configuration at it.

## Add a Vue single-file component

Create the source under the server module:

```text
klab.services.example.server/
  src/main/webui/extensions/CatalogBrowser.vue
  src/main/webui/extensions/CatalogWorkspace.vue
```

The component ID is generated from the filename: `CatalogBrowser.vue` becomes `catalog-browser`.
`CatalogWorkspace.vue` becomes `catalog-workspace` and can be referenced by a full-page record. Use
the generated ID in the corresponding Java configuration. Filenames must be unique across every
extension directory included in a build.

An extension receives one required `context` prop:

```vue
<script setup lang="ts">
import type { DashboardContext } from "@klab-dashboard/types";

const props = defineProps<{ context: DashboardContext }>();

async function loadPrivateData() {
  // The shared client refreshes and sends the Keycloak token when one exists.
  return props.context.api.get("api/example/items");
}
</script>

<template>
  <q-btn label="Load items" @click="loadPrivateData" />
</template>
```

The context provides:

| Member | Meaning |
| --- | --- |
| `config` | Immutable dashboard configuration returned by this service |
| `status` | Latest public service status, or `null` while unavailable |
| `capabilities` | Latest capabilities calculated for the current identity |
| `auth` | Reactive authentication readiness, identity, and error state |
| `api.get(path)` | JSON GET using the current token when available |
| `api.request(path, init)` | Generic authenticated fetch for other HTTP methods |
| `refresh()` | Refresh shared status and capabilities immediately |

Use Quasar components for controls and layout. Quasar and Vue are already supplied by the shell;
do not add another application root or another copy of either framework.

The same prop contract applies to dashboard panels and full-page components. A full-page component
owns the content area below the shared service header, so it should provide its own responsive
working layout rather than wrapping everything in another application shell.

## Discover extensions outside this repository

The build automatically scans the four standard server modules. A downstream service in another
directory can add one or more extension roots with `KLAB_WEBUI_EXTENSION_DIRS`. Separate multiple
directories with the platform path separator (`:` on Unix, `;` on Windows) before running the
`webui` Maven profile or `npm run build`.

Only `.vue` files under those directories are included. This source-directory path is compile-time.
Runtime modules are accepted only from trusted component archives already installed and registered
by the k.LAB component mechanism; arbitrary remote module URLs are never accepted.

## Contribute UI from an installed k.LAB component

A PF4J component installed through the k.LAB component mechanism can contribute dashboard panels
and full-page interfaces without rebuilding the hosting service. This path is separate from
`KLAB_WEBUI_EXTENSION_DIRS`: the component packages a prebuilt browser module in its `.kar`, and
its `KlabComponent` subclass publishes the corresponding manifest entries at runtime.

The component Maven project must depend on `klab.core.services` to extend `KlabComponent`. Keep the
dependency out of the `.kar`—normally with Maven `provided` scope—because the hosting service
supplies the k.LAB, PF4J, Vue, and Quasar runtimes.

### Java contribution contract

Override `webUiModules()` to declare each browser module and `configureWebUi()` to place its
component IDs in panels or pages:

```java
public final class CatalogComponent extends KlabComponent {

  public CatalogComponent(PluginWrapper wrapper) {
    super(wrapper);
  }

  @Override
  public Map<String, String> webUiModules() {
    return Map.of(
        "catalog-browser", "catalog-browser.js",
        "catalog-workspace", "catalog-workspace.js");
  }

  @Override
  public void configureWebUi(WebUiConfiguration.Builder dashboard) {
    dashboard
        .panel(
            "component-catalog",
            "Component catalog",
            "Browse resources supplied by the installed component.",
            "catalog-browser",
            200,
            false)
        .page(
            "component-catalog",
            "Component catalog",
            "Manage resources supplied by the installed component.",
            "catalog-workspace",
            200,
            true);
  }
}
```

Module IDs, panel IDs, and page names use lowercase kebab-case and must be unique within the hosting
service. The page above is linked in the dashboard header and addressed at
`/ui/component-catalog`. No Spring property or environment variable is required. The host includes
contributions from every registered component whose PF4J state is not disabled or failed.

The hosting service must initialize its `ComponentRegistry`; the standard Resources and Runtime
services currently do so. Merely constructing a registry, as some service types currently do, does
not scan or load the component repository.

### Archive and browser-module layout

Every value returned by `webUiModules()` is relative to the reserved component resource directory:

```text
my-component.kar
  META-INF/
    MANIFEST.MF
    klab/
      webui/
        catalog-browser.js
        catalog-workspace.js
  org/example/component/...
```

Only relative `.js` and `.mjs` files explicitly declared by `webUiModules()` are served. Absolute
paths, parent traversal, undeclared resources, and modules from a different component version are
rejected. The public module URL is generated by the host and includes the PF4J component ID and
version; component code should never construct that URL itself.

Each file must be a browser ESM module with the Vue component as its default export. Build it as a
self-contained file: inline local JavaScript dependencies and component CSS, but externalize
`vue`. The dashboard publishes a stable import map so the component and host use the same Vue
runtime. Quasar components such as `<q-btn>` are already registered globally. The stable
`@klab/webui` module currently exports `useQuasar`, `Dialog`, `Loading`, and `Notify`; it also
re-exports Vue's public API. Keep `vue` and `quasar` as development dependencies in the component
project so TypeScript can type-check them, but do not bundle either runtime.

If the component uses TypeScript, add this small ambient declaration until a published k.LAB UI
types artifact is available:

```ts
declare module "@klab/webui" {
  export * from "vue";
  export { Dialog, Loading, Notify, useQuasar } from "quasar";
}
```

A representative one-component Vite build is:

```ts
import path from "node:path";
import { fileURLToPath } from "node:url";
import vue from "@vitejs/plugin-vue";
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";
import { defineConfig } from "vite";

const directory = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [vue(), cssInjectedByJsPlugin()],
  build: {
    lib: {
      entry: path.resolve(directory, "src/CatalogWorkspace.vue"),
      formats: ["es"],
      fileName: () => "catalog-workspace.js",
    },
    outDir: path.resolve(directory, "../../../target/classes/META-INF/klab/webui"),
    emptyOutDir: false,
    rollupOptions: {
      external: ["vue", "@klab/webui"],
      output: { inlineDynamicImports: true },
    },
  },
});
```

Run this build before the k.LAB component packaging goal creates the classified `.kar`. If a
component contributes several UI modules, build each entry to the filename declared in
`webUiModules()`. A component that only adds a panel using a component ID already compiled into the
host may omit `webUiModules()`, but this creates a build-time coupling and is not recommended for
independently installed components.

### Runtime and security behavior

The public configuration endpoint merges service-defined entries first and installed-component
entries afterward. The Vue shell lazily imports a component module only when its panel or page is
mounted. An authentication-required full-page module is therefore not downloaded or mounted until
the Keycloak session check succeeds.

The module itself is public browser code, not an authorization boundary. Its backing REST
controllers must enforce permissions independently. Installed k.LAB components already execute as
trusted server plug-ins; their browser modules should be reviewed and versioned with the same trust
level. After installing, updating, disabling, or removing a component, reload the dashboard so it
fetches a fresh manifest. Module responses use `no-cache`, which also prevents a replaced SNAPSHOT
from being hidden by a stale browser cache.

## Authentication rules for extensions

Set `requiresAuthentication` when a component has no useful anonymous state. A dashboard panel is
replaced by a sign-in prompt. A full-page component is not mounted; after the initial `check-sso`
finishes, a persistent sign-in dialog opens over the requested URL. Keycloak returns to that exact
URL after authentication, and the shared API client then sends a standard bearer token and refreshes
it shortly before expiry.

This flag is user experience, not security. Every backing controller must still enforce the
appropriate role, CRUD permission, and resource privilege. Components should handle `401`, `403`,
empty, loading, and error responses without assuming the token grants a particular permission.

Do not store tokens in local storage, session storage, URLs, component state, logs, or persisted
Pinia/Vue state. Use `context.api` so token lifecycle remains centralized.

## Development loop

From `klab.core.services/src/main/webui`:

```bash
npm ci
npm run dev
```

The development server needs a proxy or a service origin for `/public/*` requests. Production uses
same-origin relative paths and therefore works under every service context path without CORS.

Before committing an extension:

1. Run `npm run typecheck` or the Maven `webui` profile.
2. Verify anonymous, authenticated, loading, empty, error, and narrow-screen states.
3. Confirm every protected operation is rejected server-side without a valid token.
4. Keep component IDs and the Java manifest synchronized.
5. Rebuild the core service artifact so the new compiled component is packaged.
