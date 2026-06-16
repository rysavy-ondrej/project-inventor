# Enterprise Environment Monitoring Schedules

This folder contains a set of monitoring schedules aimed at a typical
**enterprise network**. Instead of consumer/home targets, the schedules probe
the cloud and SaaS services that organisations depend on for day-to-day
operations, grouped into business-service categories.

## Tests

| File | Monitor | What it checks |
|------|---------|----------------|
| [network.ping.yaml](network.ping.yaml) | `network.ping` | Latency / reachability (ICMP echo) |
| [network.dns.yaml](network.dns.yaml)   | `network.dns`  | Name resolution via enterprise-grade resolvers |
| [security.tls.yaml](security.tls.yaml) | `security.tls` | TLS 1.3 handshake on port 443 |

Each test file defines one **schedule entry per category**, and each entry
writes to its own `enterprise.<test>.<category>` output file so results can be
analysed independently.

## Service categories

| Category | Example targets |
|----------|-----------------|
| **collaboration** | Microsoft Teams, Slack, Zoom, Webex, Gmail |
| **saas**          | Office 365, Salesforce, ServiceNow, Workday, SAP |
| **identity**      | Entra ID (login.microsoftonline.com), Okta, Duo, Ping Identity, Auth0 |
| **devops**        | GitHub, GitLab, Docker Hub, PyPI, npm registry |
| **cloud**         | AWS Console, Azure Portal, Google Cloud Console, EC2/ARM APIs |
| **security**      | Cloudflare, Zscaler, CrowdStrike Falcon, Proofpoint |

## Notes

- **DNS** queries are sent through resolvers commonly deployed in enterprise
  networks: Cisco Umbrella / OpenDNS (`208.67.222.222`), Cloudflare
  (`1.1.1.1`), Quad9 (`9.9.9.9`) and Google (`8.8.8.8`).
- **TLS** targets use `TLSv1.2` with `ECDHE-RSA-AES256-GCM-SHA384` on the
  standard HTTPS port `443`.
- **Intervals** are tightest for **identity** and **collaboration** — an SSO or
  conferencing outage blocks every downstream application — and more relaxed
  for less time-critical categories. Tune `repeat-every` to suit your
  environment.
- **Ping** caveat: many cloud/SaaS endpoints rate-limit or silently drop ICMP,
  so a failed ping does not necessarily mean an outage. Read the ping results
  alongside the DNS and TLS probes for a complete reachability picture.

## Running

These schedules use the same monitors as the other profiles, so they run the
same way — point `Run-MonitorSession.ps1` at a schedule file:

```bash
pwsh -Command "& ./Run-MonitorSession.ps1 -TestSuiteFile enterprise/network.ping.yaml | & ./Out-FileByDay.ps1 -BaseName enterprise.network.ping -OutPath ./results/"
```

or deploy the whole profile (one container per profile, results published to
Kafka) with the local installer:

```bash
deploy/autodeploy.sh   # then select the "enterprise" profile
```
