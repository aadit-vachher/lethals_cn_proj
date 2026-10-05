# Computer Networks — Phase 1

## Project Overview

This project implements a distributed client-server network across four macOS systems.

The Phase 1 infrastructure consists of:

- A private DNS server using `dnsmasq`
- An nginx HTTPS reverse proxy and load balancer
- Two REST backends
- HTTPS/TLS termination at nginx
- Round-robin load balancing
- HTTP caching using `Cache-Control`
- Network verification using `ping`, `dig`, `curl`, and Wireshark

## Team Members

- Kush Puri
- Aadit Vachher
- Aabir Sarkar
- Kushagra Maheshwari

## Network Architecture

| Machine | Role | Private IPv4 | Interface | Service |
|---|---|---|---|---|
| Mac 1 | Private DNS Server / Test Client | `10.7.22.250` | `en0` | DNS `53` |
| Mac 2 | nginx Edge / Reverse Proxy / Load Balancer | `10.3.3.0` | `en0` | HTTPS `8443` |
| Mac 3 | Backend A | `10.7.11.153` | `en0` | HTTP `3001` |
| Mac 4 | Backend B | `10.7.18.204` | `en0` | HTTP `3002` |

### DNS Names

The private DNS server resolves:

```text
app.team1.test -> 10.3.3.0
api.team1.test -> 10.3.3.0
```

Both names point to the nginx edge server.

The public DNS server does not resolve these private project names.

## Repository Structure

```text
CN-Phase1/
├── README.md
├── dns/
│   └── dnsmasq.conf
├── nginx/
│   └── nginx.conf
├── backend-a/
│   └── app.py
├── backend-b/
│   └── app.py
└── docs/
    └── architecture.md
```

## How to Run Backend A

On Mac 3:

```bash
cd backend-a
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py
```

Backend A listens on:

```text
http://10.7.11.153:3001
```

Status endpoint:

```text
http://10.7.11.153:3001/api/status
```

Backend A identifies itself using:

```text
X-Backend: A
```

## How to Run Backend B

On Mac 4:

```bash
cd backend-b
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py
```

Backend B listens on:

```text
http://10.7.18.204:3002
```

Status endpoint:

```text
http://10.7.18.204:3002/api/status
```

Backend B identifies itself using:

```text
X-Backend: B
```

## How to Run Private DNS

On Mac 1:

```bash
sudo dnsmasq --test --conf-file="$HOME/cn-project/dnsmasq.conf"
```

If the syntax check succeeds:

```bash
sudo dnsmasq --no-daemon --conf-file="$HOME/cn-project/dnsmasq.conf"
```

The DNS server listens on:

```text
10.7.22.250:53
```

Test DNS resolution:

```bash
dig @10.7.22.250 app.team1.test
dig @10.7.22.250 api.team1.test
```

Expected result:

```text
app.team1.test -> 10.3.3.0
api.team1.test -> 10.3.3.0
```

## How to Run nginx

On Mac 2:

```bash
sudo nginx -t -c "$HOME/cn-project/nginx.conf"
```

Start nginx:

```bash
sudo nginx -c "$HOME/cn-project/nginx.conf"
```

nginx listens for HTTPS traffic on:

```text
10.3.3.0:8443
```

The nginx upstream contains:

```text
10.7.11.153:3001
10.7.18.204:3002
```

## HTTPS Test

After configuring the client to use the private DNS server and trusting the project CA:

```bash
curl -v https://app.team1.test:8443
```

The final application test uses the DNS name rather than an IP address and does not require `-k`.

The TLS certificate is issued for:

```text
app.team1.test
```

## Load Balancing Test

Run multiple requests:

```bash
for i in {1..6}; do
  curl -s -D - https://app.team1.test:8443/api/status -o /dev/null | grep -E 'HTTP/|X-Backend:'
  echo
done
```

The responses should alternate between:

```text
X-Backend: A
```

and:

```text
X-Backend: B
```

This demonstrates nginx round-robin load balancing.

## HTTP Caching

The backend response includes:

```text
Cache-Control: public, max-age=60
```

Verify the header:

```bash
curl -sI https://app.team1.test:8443/api/status
```

`max-age=60` indicates that the response can be treated as fresh for 60 seconds.

## Failure Demonstration

The private DNS dependency can be demonstrated by intentionally changing the client DNS server to a public DNS resolver:

```bash
sudo networksetup -setdnsservers "Wi-Fi" 8.8.8.8
dig app.team1.test
```

The expected result is:

```text
status: NXDOMAIN
ANSWER: 0
SERVER: 8.8.8.8#53
```

This occurs because `app.team1.test` is a private project domain and is not publicly resolvable.

Restore the project DNS server:

```bash
sudo networksetup -setdnsservers "Wi-Fi" 10.7.22.250
```

## Verification

The Phase 1 system was verified using:

- Pairwise `ping` between the four machines
- Private DNS resolution using `dig`
- Direct backend HTTP requests
- HTTPS requests through nginx
- TLS certificate verification
- nginx round-robin load balancing
- HTTP `Cache-Control` headers
- Wireshark packet captures for DNS, TCP, and TLS
- DNS failure demonstration using an incorrect DNS server

