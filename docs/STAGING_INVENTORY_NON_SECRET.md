# Staging Inventory (Non-Secret)

This document captures non-secret staging details available in the repo. It does not include passwords, private keys, or sensitive credentials.

Sources:
- environments/staging/README.md
- environments/staging/config.yaml
- environments/staging/scripts/setup_wireguard.sh

## Nodes
- Staging: single-node k3s (per staging kickoff runbook)

## Network and Access (Non-Secret)
- Access mode: WireGuard-only
- VPN subnet (default): 10.88.0.0/24
- WireGuard UDP port (default): 51820
- Staging DNS host: yam-staging.vpn.internal
- Ingress host: yam-staging.vpn.internal

## Namespace
- Namespace: yam-agri-staging

## Apps and Images
- Apps installed: erpnext, agriculture, yam_agri_core, yam_agri_qms_trace
- Images:
  - frappe/erpnext:v16.5.0
  - mariadb:10.6
  - redis:6.2-alpine
  - yamagri/ai-gateway:latest
  - yamagri/iot-gateway:latest

## Storage (PVC)
- Storage class: local-path
- Sites PVC size: 20Gi
- MariaDB PVC size: 20Gi

## Accounts (Placeholders)
- SSH user: <staging_ssh_user>
- SSH host: <staging_host_or_ip>
- Frappe admin user: <staging_admin_user>
- Service accounts (k3s/system): <list_from_infra>

## Secrets (Not Stored Here)
- SSH private keys
- WireGuard server/peer private keys
- Database passwords
- App admin passwords
- API tokens

## How to Fill Real Values
- Ask IT admin/infra owner for:
  - Staging host public IP or VPN reachable IP
  - WireGuard server public key and endpoint
  - Assigned peer config for your workstation
  - SSH user and key distribution path
  - App admin account details (delivered out-of-band)

## Notes
- If DNS is unavailable, use STAGING_HOST_IP + hosts override per staging runbook.
- WireGuard peer configs are generated via setup_wireguard.sh on the staging server.
