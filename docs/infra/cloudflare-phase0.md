# Cloudflare, phase 0 : en-têtes de sécurité

Fiche pas à pas pour ajouter les en-têtes HTTP de sécurité devant GitHub Pages.
GitHub Pages ne permet pas d'envoyer d'en-têtes personnalisés ; Cloudflare, déjà
en proxy devant le site (DNS « orange cloud »), peut les ajouter à chaque réponse,
comme un `add_header` nginx ou une règle du Rules Engine d'Azure Front Door.

> **Ordre important :** appliquer ces règles **après la fusion de la PR de phase 0**.
> Cette PR retire le dernier script inline (le chargeur Mermaid) et le CDN jsDelivr ;
> sans elle, la CSP ci-dessous bloquerait les diagrammes.

## Ce qui a été vérifié avant de te le proposer

La CSP a été testée **en mode bloquant** sur un build local de la branche, avec
Chromium, sur 15 pages types : accueil, blog, recherche, articles avec Mermaid,
vidéo et audio, giscus, portfolio, CV, /now/, /sky/, une entrée APOD, une page
de tag et la 404. Résultat : **0 violation**, Mermaid et giscus s'affichent.

Seule exception connue et sans impact : les anciennes pages de redirection
générées par `jekyll-redirect-from` contiennent un script inline
`location="..."`. La CSP le bloque, mais la balise `<meta http-equiv="refresh">`
de la même page fait la redirection : vérifié, l'utilisateur arrive bien à la
nouvelle adresse.

## Étape 1 : la CSP en mode observation (une semaine)

Tableau de bord Cloudflare → domaine `dominicdapice.com` → **Rules** →
**Overview** → **Create rule** → **Response Header Transform Rule**.

- **Nom :** `security-headers`
- **If incoming requests match… :** *Custom filter expression*
  - Field `Hostname` · Operator `equals` · Value `dominicdapice.com`
- **Then… Modify response header :** une ligne par en-tête, action **Set static**

| En-tête | Valeur |
|---|---|
| `Content-Security-Policy-Report-Only` | voir ci-dessous |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=()` |
| `X-Content-Type-Options` | `nosniff` |
| `Cross-Origin-Opener-Policy` | `same-origin` |

Valeur de la CSP (une seule ligne) :

```
default-src 'self'; script-src 'self' https://gc.zgo.at https://giscus.app; style-src 'self' 'unsafe-inline' https://giscus.app; img-src 'self' data: https://dapiced.goatcounter.com; font-src 'self'; media-src 'self'; connect-src 'self' https://dapiced.goatcounter.com; frame-src https://giscus.app; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests
```

Pourquoi chaque source est là :

| Directive | Source | Raison |
|---|---|---|
| `script-src` | `gc.zgo.at` | script de comptage GoatCounter |
| `script-src`, `frame-src`, `style-src` | `giscus.app` | commentaires sous les articles |
| `connect-src`, `img-src` | `dapiced.goatcounter.com` | envoi des pages vues et compteurs de visiteurs |
| `style-src` | `'unsafe-inline'` | quelques attributs `style=""` (pastilles de langage, 404) et les styles générés par Mermaid ; à retirer en phase 1 avec le design system |
| `frame-ancestors` | `'none'` | empêche d'intégrer le site dans une iframe (clickjacking) ; n'existe qu'en en-tête, pas en `<meta>` |

**Pendant cette semaine :** ouvrir quelques pages avec les outils de
développement (F12 → Console). Une violation apparaît sous la forme
`[Report Only] Refused to ...`. S'il n'y en a pas, passer à l'étape 2.

**Retour arrière :** désactiver la règle (interrupteur dans la liste des règles),
effet en quelques secondes.

## Étape 2 : passer la CSP en mode bloquant

Dans la même règle, renommer l'en-tête `Content-Security-Policy-Report-Only`
en `Content-Security-Policy`, même valeur.

## Étape 3 : HSTS sur 12 mois

Aujourd'hui `Strict-Transport-Security: max-age=2592000` (30 jours), envoyé par
Cloudflare sur `dominicdapice.com`, `www` et `app`.

**SSL/TLS** → **Edge Certificates** → **HTTP Strict Transport Security (HSTS)** :

- Max Age : **12 months**
- Apply HSTS policy to subdomains (includeSubDomains) : **On**. Vérifié :
  `www.dominicdapice.com` et `app.dominicdapice.com` répondent en HTTPS et
  redirigent `http://` vers `https://`.
- Preload : **Off** pour l'instant. Le preload inscrit le domaine dans les
  navigateurs pour des mois et se défait difficilement ; on l'envisagera quand
  tous les sous-domaines futurs seront connus.
- No-Sniff header : **On**.

Vérifier aussi dans **SSL/TLS** → **Edge Certificates** : *Always Use HTTPS* sur
**On**, *Minimum TLS Version* sur **TLS 1.2**.

## Vérification

```bash
curl -sI https://dominicdapice.com/ | grep -iE 'content-security|referrer|permissions|strict-transport|cross-origin'
```

Puis un passage sur <https://developer.mozilla.org/en-US/observatory> (cible : A ou mieux).

## Pour plus tard (phases suivantes)

- **Cache Rules** : mettre le HTML en cache à l'edge (2 h) et vider le cache à
  la fin de chaque déploiement, avec un jeton API limité à *Zone > Cache Purge*.
- **Cloudflare Pages** : préproduction par PR, jeton limité à *Cloudflare Pages > Edit*.
- **Terraform** : ces règles décrites en code (`cloudflare_ruleset`), avec
  `terraform plan` sur chaque PR et `apply` manuel.

Aucun jeton n'est nécessaire pour la phase 0 : tout se fait dans le tableau de bord.
