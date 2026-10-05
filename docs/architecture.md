# Phase 1 Network Architecture

## 1. Overview

The Phase 1 implementation uses four macOS systems connected through a private network.

The architecture separates DNS, edge proxy/load-balancing, and application backend responsibilities across the four machines.

```text
                         Private DNS
                      Mac 1 — 10.7.22.250
                         dnsmasq :53
                              |
                              | DNS
                              v
                    app.team1.test
                    api.team1.test
                              |
                              v
                 +-------------------------+
                 | Mac 2 — 10.3.3.0       |
                 | nginx Edge              |
                 | HTTPS :8443             |
                 | Reverse Proxy / LB      |
                 +------------+------------+
                              |
                    Round-Robin HTTP
                       /             \
                      /               \
                     v                 v
       +----------------------+   +----------------------+
       | Mac 3                |   | Mac 4                |
       | 10.7.11.153          |   | 10.7.18.204          |
       | Backend A            |   | Backend B            |
       | HTTP :3001           |   | HTTP :3002           |
       +----------------------+   +----------------------+
```

## 2. Machine Roles

### Mac 1 — Private DNS

**IP:** `10.7.22.250`

**Interface:** `en0`

**Service:** dnsmasq on UDP/TCP port `53`

Mac 1 provides private DNS resolution for the project domain.

The configured records are:

```text
app.team1.test -> 10.3.3.0
api.team1.test -> 10.3.3.0
```

Both application names therefore direct clients to the nginx edge server.

### Mac 2 — Edge / Reverse Proxy / Load Balancer

**IP:** `10.3.3.0`

**Interface:** `en0`

**Service:** nginx HTTPS on port `8443`

Mac 2 is the single application entry point.

It terminates TLS and forwards HTTP requests to the backend pool:

```text
10.7.11.153:3001
10.7.18.204:3002
```

nginx uses round-robin distribution between the two backend servers.

### Mac 3 — Backend A

**IP:** `10.7.11.153`

**Interface:** `en0`

**Service:** HTTP on port `3001`

Backend A exposes:

```text
/api/status
```

The response contains:

```text
X-Backend: A
```

### Mac 4 — Backend B

**IP:** `10.7.18.204`

**Interface:** `en0`

**Service:** HTTP on port `3002`

Backend B exposes:

```text
/api/status
```

The response contains:

```text
X-Backend: B
```

## 3. Request Flow

A normal application request follows this sequence:

```text
Client
  |
  | DNS query
  v
Mac 1 — dnsmasq
  |
  | app.team1.test -> 10.3.3.0
  v
Mac 2 — nginx
  |
  | TLS termination
  |
  | HTTP proxy request
  v
Backend A or Backend B
```

The client does not need to directly address the backend machines.

## 4. DNS Resolution

The private DNS server provides authoritative local answers for the project names.

Example:

```bash
dig app.team1.test
```

Expected result:

```text
app.team1.test.    IN    A    10.3.3.0
```

The project domain is intentionally private. A public resolver such as `8.8.8.8` does not provide the project record.

## 5. HTTPS and TLS

HTTPS is terminated at nginx on Mac 2.

The service is accessed as:

```text
https://app.team1.test:8443
```

The server certificate is configured for the application hostname.

The TLS connection protects the HTTP request and response between the client and nginx.

Wireshark can show the TCP connection and TLS handshake metadata, including ClientHello, ServerHello, Certificate, and TLS Application Data. The HTTP payload is encrypted after the TLS handshake.

## 6. Load Balancing

nginx maintains an upstream pool containing:

```text
10.7.11.153:3001
10.7.18.204:3002
```

Requests are distributed using nginx's default round-robin behavior.

The backend identity can be observed through:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

Repeated requests demonstrate that both backend servers receive traffic.

## 7. HTTP Caching

The `/api/status` response provides:

```text
Cache-Control: public, max-age=60
```

This allows a client or intermediary cache to treat the response as fresh for 60 seconds.

The header can be verified using:

```bash
curl -I https://app.team1.test:8443/api/status
```

## 8. Failure Scenario

The DNS dependency is demonstrated by changing the client DNS server from the private DNS server to a public resolver.

For example:

```bash
sudo networksetup -setdnsservers "Wi-Fi" 8.8.8.8
dig app.team1.test
```

The result is:

```text
status: NXDOMAIN
ANSWER: 0
SERVER: 8.8.8.8#53
```

This demonstrates that the project hostname depends on the private DNS infrastructure.

The client is restored with:

```bash
sudo networksetup -setdnsservers "Wi-Fi" 10.7.22.250
```

## 9. Verification and Observability

The architecture was verified using:

- ICMP ping between the four machines
- DNS queries using `dig`
- Direct HTTP backend requests
- HTTPS requests using the project hostname
- TLS certificate verification
- Repeated requests to demonstrate load balancing
- HTTP response-header inspection using `curl -I`
- Wireshark captures of DNS, TCP, and TLS traffic

## 10. Configuration Files

The repository contains the main configuration/source files used by the Phase 1 system:

```text
dns/dnsmasq.conf
nginx/nginx.conf
backend-a/app.py
backend-b/app.py
```

These files correspond to the services running on the four project machines.