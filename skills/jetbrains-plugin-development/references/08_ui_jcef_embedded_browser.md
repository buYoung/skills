# Embedded Browser with JCEF

Read this when a plugin embeds Chromium-based HTML rendering in Swing UI, such as Markdown
preview, generated HTML preview, diagrams, or web-based custom components.

## When to use

Use standard IntelliJ Platform Swing UI first. Choose JCEF only when the feature genuinely
needs HTML/browser rendering or a web component that Swing cannot reasonably provide.

`JBCefApp` manages JCEF initialization. Check `JBCefApp.isSupported()` before using JCEF and
provide a fallback when unsupported. JCEF can be missing when the IDE runs on a JDK without a
compatible JCEF build.

## Browser and client lifecycle

Use `JBCefBrowser` or `JBCefBrowserBuilder` for browser instances. The default implicit
client is disposed with the browser. A custom `JBCefClient` must be disposed explicitly by
plugin code.

Register handlers through the supported JCEF APIs and dispose them with the browser or
client. Treat browser handlers as lifecycle-sensitive resources, especially in tool windows
and custom file editors.

## JavaScript bridge

Use `JBCefJSQuery` for JavaScript-to-plugin callbacks when the page needs to invoke plugin
logic. Validate inputs, handle failure responses, and avoid exposing broad project actions
to arbitrary page content. Local file links and external links should be routed deliberately.

## Diagnostics checklist

1. Confirm JCEF is necessary and supported in the running IDE.
2. Provide a non-JCEF fallback or user-facing disabled state.
3. Dispose custom clients, handlers, and browser resources.
4. Avoid loading untrusted HTML with privileged callbacks.
5. Test dynamic plugin unload and tool-window/editor close paths for leaks.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/embedded-browser-jcef.html
