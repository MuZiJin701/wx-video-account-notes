# ADR 0004: Browser login for the self-deployed resolver

Status: Accepted

Keep the self-deployed service on Linux x64 with systemd, retaining the Go resolver and gateway. Add Playwright-controlled headless Chromium to obtain Yuanbao Cookie through QQ login, with QQ login credentials supplied in a server-side configuration file during deployment. This keeps browser authentication separate from share-link resolution and avoids replacing the working resolver.

Playwright launches a dedicated Chromium in new headless mode, using a persistent private browser profile. Maintenance runs once immediately after the first deployment and daily thereafter, with the interval configurable. It reuses the existing Cookie while valid and updates it after login expires. A network or upstream failure alone is not evidence of an expired login; retain the previous Cookie when validity cannot be established. Replacement Cookie must pass the existing resolver check before atomic publication, and replacement failure preserves the previous file.

Keep all operator-supplied server configuration in one private `config.json`: the resolver access key, one QQ account and password, the maintenance interval, and a verification share link. Cookie and the browser profile remain separate private runtime state. The client continues to hold only its resolver endpoint and access key. Preserve existing credentials and runtime state during upgrades from `client.json`; QQ credentials and browser dependencies belong only on the server.

The login flow skips the optional phone-binding step observed in the existing experiment. Password errors, non-skippable verification, or a changed page flow report a failure and suspend automatic password retries until manual recovery; periodic checks may still reuse a valid existing Cookie. Keep the manual Cookie update entry point. Secrets and browser state must stay out of Git and logs.

On the first occurrence of a maintenance error, attempt a self-addressed QQ Mail notification using Playwright and the same QQ credentials, with a separate persistent browser profile. Include only a timestamp and a fixed error code. Mark the attempt before sending, suppress repeat notifications for the same unresolved error, and log delivery failure without recursively notifying. A paused-login status does not create another alert. This avoids another mail secret at the cost of making notification depend on QQ web login; do not treat it as guaranteed delivery.

Daily checks allow nearly a day between an unexpected expiry and the next automatic recovery attempt. The existing Windows headed-browser experiment does not establish Linux headless support; controlled real-login validation is still needed in addition to offline regression checks.
