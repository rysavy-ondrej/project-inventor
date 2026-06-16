# Czech Enterprise Environment Monitoring Schedules

This folder is a **Czech-localised** variant of [../enterprise](../enterprise).
It keeps the globally-used corporate services (Microsoft 365, GitHub, AWS,
Okta, ...) but adds the services and statutory portals that actually matter to
a company operating in the Czech Republic — the **datové schránky** (data
boxes), Finanční správa, ČSSZ, ARES, Identita občana, Czech ERP/accounting
vendors and Czech hosting providers — and resolves through the CZ.NIC ODVR
resolver.

## Tests

| File | Monitor | What it checks |
|------|---------|----------------|
| [network.ping.yaml](network.ping.yaml) | `network.ping` | Latency / reachability (ICMP echo) |
| [network.dns.yaml](network.dns.yaml)   | `network.dns`  | Name resolution via enterprise + CZ.NIC resolvers |
| [security.tls.yaml](security.tls.yaml) | `security.tls` | TLS 1.3 handshake on port 443 |

Each test file defines one **schedule entry per category** and writes to its
own `enterprise.cz.<test>.<category>` output file.

## Service categories

| Category | Czech-relevant targets |
|----------|------------------------|
| **collaboration** | Microsoft Teams, Slack, Zoom, Webex, Gmail |
| **saas**          | Office 365, Salesforce, **Pohoda (Stormware)**, **Money (Solitea)**, **ABRA** |
| **identity**      | Entra ID, Okta, **Identita občana (eidentita.cz)**, Duo, Auth0 |
| **devops**        | GitHub, GitLab, Docker Hub, PyPI, npm registry |
| **cloud**         | Azure, AWS, Google Cloud, **WEDOS**, **Active24**, **FORPSI** |
| **egov**          | **Datová schránka**, **Finanční správa**, **ČSSZ**, **ARES**, **Portál občana** |
| **security**      | Cloudflare, Zscaler, CrowdStrike, Proofpoint, **NÚKIB** |

### Differences from the generic `enterprise` suite

- **Added — Czech ERP/SaaS**: Stormware Pohoda, Solitea Money, ABRA (the
  dominant accounting/ERP vendors in CZ).
- **Added — Czech identity**: Identita občana / NIA (`eidentita.cz`), the
  national identity gateway used for government and many corporate logins.
- **Added — Czech hosting/cloud**: WEDOS, Active24, FORPSI alongside the
  hyperscalers.
- **Added — new `egov` category**: the statutory portals a Czech company is
  legally required to interact with — **datové schránky**
  (`mojedatovaschranka.cz`), **Finanční správa** (tax), **ČSSZ** (social
  security), **ARES** (business registry) and **Portál občana**.
- **Added — NÚKIB**: the Czech National Cyber and Information Security Agency,
  in the `security` category.

## Notes

- **DNS** adds the **CZ.NIC ODVR** open resolver (`193.17.47.1`) alongside
  Google (`8.8.8.8`), Cloudflare (`1.1.1.1`) and Quad9 (`9.9.9.9`); `.cz`
  domains are resolved through it.
- **TLS** targets use `TLSv1.2` with `ECDHE-RSA-AES256-GCM-SHA384` on port
  `443`. **Identity** and **egov** run at tighter intervals — a TLS failure on
  the SSO gateway or a statutory portal blocks business-critical access.
- **Ping** caveat: many cloud and Czech eGovernment endpoints rate-limit or
  silently drop ICMP, so a failed ping does not necessarily mean an outage.
  Read the ping results alongside the DNS and TLS probes.

## Running

Same mechanism as the rest of the testbed — point `Run-MonitorSession.ps1` at a
schedule file:

```bash
pwsh -Command "& ./Run-MonitorSession.ps1 -TestSuiteFile enterprise.cz/network.ping.yaml | & ./Out-FileByDay.ps1 -BaseName enterprise.cz.network.ping -OutPath ./results/"
```

or deploy the whole profile (one container per profile, results published to
Kafka) with the local installer:

```bash
deploy/autodeploy.sh   # then select the "enterprise.cz" profile
```
