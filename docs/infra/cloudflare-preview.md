# Cloudflare Pages : préproduction par pull request

Chaque PR est construite puis publiée sur un projet Cloudflare Pages **séparé**,
avec une adresse du type `https://pr-125.dominicdapice-preview.pages.dev`. Un
commentaire sur la PR donne le lien et se met à jour à chaque push. La production
reste sur GitHub Pages et ne change pas.

Analogie Azure : un *deployment slot* de staging sur App Service, détruit à la fin.

Le workflow `.github/workflows/preview.yml` est **inactif** tant que les étapes
ci-dessous ne sont pas faites : sa première étape vérifie la variable
`CLOUDFLARE_ACCOUNT_ID` et le secret `CLOUDFLARE_PAGES_TOKEN`, et indique dans le
journal ce qui manque.

## Ce que tu fais (environ 10 minutes, une seule fois)

### 1. Le projet Pages (automatique)

Rien à faire : au premier déploiement, le workflow crée lui-même le projet
`dominicdapice-preview` (Direct Upload, sans connexion Git) s'il n'existe pas.
Il apparaît ensuite dans **Workers & Pages**.

### 2. Relever l'Account ID

**Workers & Pages** → colonne de droite, **Account ID** (32 caractères
hexadécimaux). Ce n'est pas un secret, mais il identifie ton compte.

### 3. Créer un jeton API à permission unique

Un **jeton de compte** (Account API Token), pas un jeton utilisateur : un jeton
créé dans *My Profile → API Tokens*, même avec la bonne permission, a été refusé
par l'API Pages (`10000 Authentication error`) sur ce compte.

Compte → **Manage account** → **Account API tokens** → **Create Token** →
**Start from scratch (Custom)**.

| Champ | Valeur |
|---|---|
| Token name | `github-actions-pages-preview-account` |
| Permissions | **Account** · **Cloudflare Pages** · **Edit** (et rien d'autre ; le premier menu doit être *Account*, pas *User* ni *Zone*) |
| Client IP Address Filtering | vide (les runners GitHub changent d'IP) |
| TTL | une date d'expiration, par exemple dans 1 an (à noter pour le renouveler) |

**Continue to summary** → **Create Token**, puis copie le jeton : il n'est
affiché qu'une fois. Ne le colle nulle part ailleurs que dans GitHub (étape 4).

Ce jeton ne peut **que** déployer des projets Pages : il n'a aucun accès au DNS,
aux règles de sécurité, au cache ni au domaine `dominicdapice.com`.

### 4. Le ranger dans GitHub

Dépôt `dapiced/dapiced.github.io` → **Settings** :

1. **Environments** → **New environment** → nom : `preview` → **Configure environment**
   → **Environment secrets** → **Add environment secret** :
   - Name : `CLOUDFLARE_PAGES_TOKEN`
   - Value : le jeton de l'étape 3
2. **Secrets and variables** → **Actions** → onglet **Variables** →
   **New repository variable** :
   - Name : `CLOUDFLARE_ACCOUNT_ID`
   - Value : l'Account ID de l'étape 2

Ne mets pas de « Required reviewers » sur l'environnement `preview`, sinon chaque
aperçu attendrait une approbation manuelle.

### 5. Vérifier

Ouvre ou mets à jour n'importe quelle PR : le job **Preview / Deploy preview**
s'exécute, puis un commentaire « **Preview:** https://pr-…pages.dev » apparaît.

## Sécurité

- **Jeton minimal :** permission *Cloudflare Pages · Edit* seulement, avec date d'expiration,
  révocable en un clic dans **Account API tokens**.
- **Secret confiné :** il est stocké dans l'environnement `preview`, jamais dans le dépôt. Les PR
  venant de forks et celles de Dependabot ne le reçoivent pas et sont ignorées.
- **Aucun risque SEO :** les aperçus envoient `X-Robots-Tag: noindex, nofollow`, pas de
  contenu dupliqué indexé.
- **Coût :** 0 $. Le build se fait dans GitHub Actions ; Cloudflare ne fait
  qu'héberger les fichiers.

## Ménage (optionnel)

Les anciens aperçus restent consultables dans **Workers & Pages** →
`dominicdapice-preview` → **Deployments**, où ils peuvent être supprimés.

## Renouveler le jeton

Le jeton `github-actions-pages-preview-account` a une date d'expiration (environ un an après
sa création, en octobre 2027). Quand il expire, le job **Preview / Deploy preview**
échoue avec une erreur d'authentification Cloudflare ; la production n'est pas touchée.

1. Cloudflare → **Manage account** → **Account API tokens** → ligne `github-actions-pages-preview-account`
   → **⋯** → **Roll** (ou **Edit** pour prolonger la date d'expiration).
2. GitHub → **Settings** → **Environments** → `preview` → secret
   `CLOUDFLARE_PAGES_TOKEN` → ✏️ → coller le nouveau jeton.

Règle : un jeton qui a été affiché ailleurs que dans ces deux écrans (capture, message,
fichier) se régénère immédiatement avec **Roll**.

## Dépannage

| Symptôme | Cause probable | Correction |
|---|---|---|
| Le job **Deploy preview** se termine en quelques secondes avec la notice « Preview disabled » | La notice nomme ce qui manque : variable `CLOUDFLARE_ACCOUNT_ID` (souvent créée par erreur sous *Secrets and variables → Agents*, ou avec une faute de frappe dans le nom, par exemple `CLOUDFARE_…` sans le L) et/ou secret `CLOUDFLARE_PAGES_TOKEN` | Variable : **Settings → Secrets and variables → Actions → Variables** (l'adresse finit par `/settings/variables/actions`) ou variable de l'environnement `preview`. Secret : environnement `preview`. Pousser ensuite un commit sur la PR. |
| « Authentication error » au déploiement | Jeton expiré, révoqué ou mal collé | Voir « Renouveler le jeton ». |
| « Pages API refused », `10000 Authentication error`, ou `9109 Invalid access token` pour la liste des comptes | Le jeton est actif mais n'a aucune permission de niveau compte (permission *User* ou *Zone*, ou mauvais jeton collé) | Créer un jeton de compte (**Account API tokens**) avec **Cloudflare Pages · Edit** (étape 3) et remplacer le secret. Le résumé avant création doit afficher `<compte> - Cloudflare Pages:Edit`. |
| « Project creation failed » | Nom déjà pris sur `pages.dev` ou quota atteint | Définir la variable `CLOUDFLARE_PAGES_PROJECT` avec un autre nom. |
| Pas de commentaire sur la PR | Le déploiement a échoué avant | Lire le journal du job **Deploy preview**. |
