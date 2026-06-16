# Czech Home Environment Monitoring Schedules

This folder is a **Czech-localised** variant of [../home](../home). It keeps the
globally-used services (Netflix, YouTube, Steam, Facebook, ...) but drops
US-only services that Czech home users rarely touch (Walmart, eBay, CNN,
NYTimes, ...) and adds the services that actually dominate Czech households —
Seznam, Alza, Novinky, Česká televize, Voyo, Czech banks, and more.

## Tests

| File | Monitor | What it checks |
|------|---------|----------------|
| [network.ping.yaml](network.ping.yaml) | `network.ping` | Latency / reachability (ICMP echo) |
| [network.dns.yaml](network.dns.yaml)   | `network.dns`  | Name resolution via common public resolvers |
| [security.tls.yaml](security.tls.yaml) | `security.tls` | TLS 1.3 handshake on port 443 |

Each test file defines one **schedule entry per category** and writes to its
own `home.cz.<test>.<category>` output file.

## Service categories

| Category | Czech-relevant targets |
|----------|------------------------|
| **streaming** | Netflix, YouTube, **Voyo (Nova)**, **Česká televize**, Spotify, Max (HBO) |
| **gaming**    | Steam, PlayStation, Xbox, Epic Games, Nintendo, Riot Games |
| **social**    | Facebook, Instagram, TikTok, Reddit, X, Discord |
| **news**      | **Novinky**, **iDNES**, **Seznam Zprávy**, **Aktuálně**, **ČT24**, **iROZHLAS** |
| **shopping**  | **Alza**, **Mall**, **CZC**, **Heureka**, **Rohlík**, **Notino** |
| **banking**   | **ČSOB**, **Komerční banka**, **Česká spořitelna**, **MONETA**, **Air Bank**, **Fio** |
| **cloud**     | Google, **Seznam**, Outlook/Office 365, iCloud, Dropbox, Zoom |

### Differences from the generic `home` suite

- **Removed** (US-only, little used in CZ): Walmart, eBay, AliExpress, CNN,
  NYTimes, BBC, Disney+, Prime Video, Google News, The Guardian.
- **Added** (Czech): Seznam (portal/email), Alza/Mall/CZC/Heureka/Rohlík/Notino
  (shopping), Novinky/iDNES/Seznam Zprávy/Aktuálně/ČT24/iROZHLAS (news), Voyo +
  Česká televize (streaming), and a new **banking** category with the six
  largest Czech retail banks.

## Notes

- **DNS** adds the **CZ.NIC ODVR** open resolver (`193.17.47.1`) alongside
  Google (`8.8.8.8`) and Cloudflare (`1.1.1.1`), since CZ.NIC's resolver is a
  common choice in Czech homes; Czech `.cz` domains are resolved through it.
- **TLS** targets use `TLSv1.2` with `ECDHE-RSA-AES256-GCM-SHA384` on port
  `443`. The **banking** category runs at a tighter interval given its
  security relevance.
- **Ping** intervals are tighter for interactive categories (streaming,
  gaming, cloud) and more relaxed for the rest. Tune `repeat-every` as needed.

## Running

Same mechanism as the rest of the testbed — point `Run-MonitorSession.ps1` at a
schedule file:

```bash
pwsh -Command "& ./Run-MonitorSession.ps1 -TestSuiteFile home.cz/network.ping.yaml | & ./Out-FileByDay.ps1 -BaseName home.cz.network.ping -OutPath ./results/"
```

or add a corresponding service to `docker-compose.yaml`.
