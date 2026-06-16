# Home Environment Monitoring Schedules

This folder contains a set of basic monitoring schedules aimed at a typical
**home network**. Instead of institutional targets, the schedules probe the
online services that ordinary home users connect to every day, and group them
into a handful of service categories.

## Tests

| File | Monitor | What it checks |
|------|---------|----------------|
| [network.ping.yaml](network.ping.yaml) | `network.ping` | Latency / reachability (ICMP echo) |
| [network.dns.yaml](network.dns.yaml)   | `network.dns`  | Name resolution via common public resolvers |
| [security.tls.yaml](security.tls.yaml) | `security.tls` | TLS 1.3 handshake on port 443 |

Each test file defines one **schedule entry per category**, and each entry
writes to its own `home.<test>.<category>` output file so results can be
analysed independently.

## Service categories

| Category | Example targets |
|----------|-----------------|
| **streaming** | Netflix, YouTube, Disney+, Prime Video, Twitch, Spotify |
| **gaming**    | Steam, PlayStation, Xbox, Epic Games, Nintendo, Riot Games |
| **social**    | Facebook, Instagram, TikTok, Reddit, X, Discord |
| **news**      | BBC, CNN, NYTimes, The Guardian, Google News |
| **shopping**  | Amazon, eBay, AliExpress, Walmart |
| **cloud**     | Google, Outlook/Office 365, iCloud, Dropbox, Zoom |

## Notes

- **DNS** queries are sent through the public resolvers a home user is most
  likely to be configured with: Google (`8.8.8.8`), Cloudflare (`1.1.1.1`)
  and Quad9 (`9.9.9.9`).
- **TLS** targets use `TLSv1.2` with `ECDHE-RSA-AES256-GCM-SHA384` on the
  standard HTTPS port `443`.
- **Ping** intervals are tighter for interactive categories (streaming,
  gaming, cloud) and more relaxed for less latency-sensitive ones (news,
  shopping). Tune `repeat-every` to suit your needs.

## Running

These schedules use the same monitors as the top-level
[../schedules](../schedules) suite, so they run the same way — point
`Run-MonitorSession.ps1` at a schedule file:

```bash
pwsh -Command "& ./Run-MonitorSession.ps1 -TestSuiteFile home/network.ping.yaml | & ./Out-FileByDay.ps1 -BaseName home.network.ping -OutPath ./results/"
```

or add a corresponding service to `docker-compose.yaml`.
