# Site

Jeu web statique (GitHub Pages / nom de domaine perso) avec login user/admin.

## Synchronisation multi-appareils

Le projet sauvegarde localement dans le navigateur, mais il supporte aussi une synchro temps reel entre appareils via Firebase Realtime Database.

### 1) Creer Firebase

1. Cree un projet Firebase.
2. Active Realtime Database.
3. Dans Project settings > General, ajoute une app Web et copie la config JavaScript.

### 2) Activer la config dans [index.html](index.html)

Dans [index.html](index.html), remplace:

```js
window.SITE_SYNC_CONFIG = window.SITE_SYNC_CONFIG || null;
```

par:

```js
window.SITE_SYNC_CONFIG = {
	firebaseConfig: {
		apiKey: "...",
		authDomain: "...",
		databaseURL: "...",
		projectId: "...",
		appId: "..."
	},
	dbPath: "pour-anna/prod"
};
```

### 3) Regles de securite minimales (test)

Exemple simple pour tester rapidement:

```json
{
	"rules": {
		".read": true,
		".write": true
	}
}
```

Pour la prod, restreins les regles (IP, auth, ou structure plus fine).

### Resultat

- Admin et utilisateur voient le meme etat sur des appareils differents.
- Un meme compte connecte sur plusieurs appareils garde les memes informations.
