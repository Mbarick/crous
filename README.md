# Crous Watch

Surveille une page de résultats sur trouverunlogement.lescrous.fr et t'envoie
une alerte (notification téléphone + email) dès qu'un nouveau logement
apparaît. Vérification automatique toutes les 15 minutes, gratuit, hébergé
sur GitHub Actions.

## 1. Récupérer ton URL de recherche

1. Va sur https://trouverunlogement.lescrous.fr
2. Lance une recherche pour la ville (et les filtres) qui t'intéressent
   (prix, type de logement, etc.)
3. Copie l'URL complète depuis la barre d'adresse de ton navigateur.
   Elle doit ressembler à :
   `https://trouverunlogement.lescrous.fr/tools/45/search?...`
4. Garde-la, tu en auras besoin à l'étape 4.

Plus la recherche est précise (ville/filtres), moins il y a de pages à
vérifier à chaque passage, et plus c'est rapide et léger.

## 2. Créer le topic ntfy (notification téléphone)

1. Installe l'app **ntfy** (gratuite, iOS et Android) ou va sur https://ntfy.sh
2. Choisis un nom de topic unique et difficile à deviner, par exemple
   `crous-tonprenom-9f3k2` (n'importe qui connaissant ce nom pourrait sinon
   voir tes notifications, car ntfy.sh est un service public).
3. Dans l'app, ajoute un abonnement à ce topic (serveur : `ntfy.sh`).

## 3. Créer un mot de passe d'application Gmail (notification email)

1. Active la validation en deux étapes sur ton compte Google si ce n'est pas
   déjà fait : https://myaccount.google.com/security
2. Va sur https://myaccount.google.com/apppasswords
3. Crée un mot de passe d'application (nom libre, ex. "crous-watch")
4. Copie le mot de passe à 16 caractères généré — c'est lui qu'on utilisera,
   jamais ton vrai mot de passe Gmail.

(Tu peux utiliser n'importe quelle adresse Gmail, y compris une adresse
secondaire créée juste pour l'occasion.)

## 4. Créer le dépôt GitHub et y déposer les fichiers

1. Crée un compte GitHub si tu n'en as pas (gratuit) : https://github.com
2. Crée un nouveau dépôt (bouton "New repository"), nomme-le par exemple
   `crous-watch`. Choisis **Public** (Actions illimité gratuitement ; le
   contenu de ce dépôt ne contient aucune information sensible, les secrets
   sont stockés séparément et restent cachés même sur un dépôt public).
3. Mets-y tous les fichiers de ce dossier, en conservant l'arborescence
   (important : `.github/workflows/crous-watch.yml` doit rester à cet
   emplacement exact).
   - Le plus simple : clique sur "Add file" → "Upload files" dans GitHub et
     dépose tout le dossier. Si l'upload web ne garde pas le sous-dossier
     `.github`, utilise plutôt "Add file" → "Create new file" et tape
     directement `.github/workflows/crous-watch.yml` comme nom de fichier
     (GitHub crée les dossiers automatiquement), puis colle le contenu.

## 5. Ajouter les secrets

Dans ton dépôt : **Settings → Secrets and variables → Actions → New
repository secret**. Ajoute ces 5 secrets :

| Nom du secret | Valeur |
|---|---|
| `SEARCH_URL` | l'URL copiée à l'étape 1 |
| `NTFY_TOPIC` | le nom de topic choisi à l'étape 2 |
| `GMAIL_ADDRESS` | ton adresse Gmail |
| `GMAIL_APP_PASSWORD` | le mot de passe d'application généré à l'étape 3 |
| `NOTIFY_EMAIL_TO` | l'adresse email où recevoir les alertes (peut être la même que GMAIL_ADDRESS) |

## 6. Tester

1. Va dans l'onglet **Actions** de ton dépôt.
2. Si demandé, clique pour activer les workflows.
3. Sélectionne "Crous Watch" puis **Run workflow** pour le lancer
   manuellement une première fois.
4. Vérifie les logs du run : tu devrais voir le nombre de logements trouvés.
5. Le premier run va considérer TOUS les logements actuellement en ligne
   comme "nouveaux" → tu vas recevoir une grosse notification une seule fois.
   C'est normal. Ensuite, tu ne seras alerté que pour les vraies nouveautés.

Une fois que c'est validé, le workflow tournera seul toutes les 15 minutes,
24h/24, sans que tu aies besoin de garder ton ordinateur ou ton téléphone
allumé.

## Pour s'arrêter

Une fois que tu as trouvé un logement : va dans **Actions → Crous Watch →
"..." → Disable workflow**, pour libérer les ressources gratuitement (et
éviter de continuer à solliciter le site Crous pour rien).

## Limites à connaître

- Si le Crous change la structure de son site, le script peut avoir besoin
  d'un petit ajustement (peu probable à court terme, mais possible).
- Sans authentification, tu vois l'offre "publique" du site (celle visible
  sans connexion) — c'est cette même offre qui s'applique en phase
  complémentaire pour les étudiants internationaux.
- Reste raisonnable sur la fréquence (15 min est déjà très réactif) pour ne
  pas solliciter excessivement le serveur du Crous.
