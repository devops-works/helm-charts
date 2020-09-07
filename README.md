# chart-cert-manager-issuer

This helm chart create issuers for [cert-manager](https://cert-manager.io/).

## Values

|Parameter|Description|Default|
|:---|:---|:---|
|email|Default register email|null (required)|
|issuer|Cert-manager issuer configuration|{}|

## Issuer configuration

`issuer` configuration object is one of the official `cert-manager` configuration :

- acme `http01` : [https://cert-manager.io/docs/configuration/acme/http01/](https://cert-manager.io/docs/configuration/acme/http01/)
- acme `dns01` : [https://cert-manager.io/docs/configuration/acme/dns01/](https://cert-manager.io/docs/configuration/acme/dns01/)

For example :

```yaml
issuers:
  - kind: ClusterIssuer
    # optional override, otherwise values.email is used
    # email: ""
    name: letsencrypt-staging
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    method:
      - http01:
          ingress:
            class: nginx
   - kind: ClusterIssuer
     # optional override, otherwise values.email is used
     # email: ""
     name: letsencrypt-prod
     server: https://acme-v02.api.letsencrypt.org/directory
     method:
        - dns01:
            clouddns:
              # The ID of the GCP project
              project: PROJECT_ID
              # This is the secret used to access the service account
              # kubectl create secret generic clouddns-dns01-solver-svc-acct \
              # --from-file=key.json -n cert-manager
              serviceAccountSecretRef:
                name: clouddns-dns01-solver-svc-acct
                key: key.json
```
