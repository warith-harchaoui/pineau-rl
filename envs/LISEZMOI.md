# Environnements figés

*English version: [README.md](README.md)*

Quatre environnements Python ont fait tourner ce projet, tous sous Python 3.11.18, sur un Mac à puce
Apple M2 Max (macOS 27.2, arm64). Chaque fichier ci-dessous est le `pip freeze` de l'un d'eux, relevé le
15 novembre 2026, avec en tête la version de Python et la plateforme.

| Fichier | Environnement | Ce qu'il fait tourner | Versions clés |
|---|---|---|---|
| `train.txt` | `sim/env` | l'entraînement (`sim/run.py`, `sim/dose.py`) | Stable-Baselines3 2.9.2, SBX 0.28.0, JAX 0.10.2, Gymnasium 1.1.1, MuJoCo 4.0.0, PyTorch 2.15.0 |
| `analysis.txt` | `sim/env-an` | tous les scripts d'analyse, `docs/check_numbers.py`, l'intégration continue | NumPy 2.4.6, SciPy 1.17.1, statsmodels 0.15.0, rliable 1.2.0 |
| `zoo.txt` | `sim/env-zoo` | la chaîne officielle de RL Baselines3 Zoo, pour l'expérience E6 | rl_zoo3 2.9.2, mêmes bibliothèques que `train.txt` |
| `llm.txt` | `sim/env-llm` | GRPO (`sim/llm/grpo.py`) et les figures de `docs/` | PyTorch 2.15.0, Transformers 5.22.2, Accelerate 1.15.0 |
| `test.txt` | par-dessus `analysis.txt` | les tests unitaires (`tests/`) | pytest 9.2.0 |

## Recréer un environnement

```bash
python3.11 -m venv sim/env-an
sim/env-an/bin/pip install -r envs/analysis.txt -r envs/test.txt
make verify            # recalcule chaque chiffre et compare les JSON octet par octet
```

Les trois autres suivent le même modèle : `sim/env` depuis `train.txt`, `sim/env-zoo` depuis `zoo.txt`,
`sim/env-llm` depuis `llm.txt`. Les chemins comptent : scripts et lanceurs appellent
`sim/env/bin/python` et ses voisins.

Les originaux viennent de conda (`conda create -p sim/env python=3.11`), puis pip a installé chaque
paquet. Un simple `venv` obtient les mêmes paquets. `sim/env-zoo` est un `venv` construit sur le Python
de `sim/env`.

## À savoir avant d'installer

- **Les mêmes listes, sous deux noms.** Les quatre fichiers reprennent `sim/requirements.lock`,
  `sim/requirements-analysis.lock`, `sim/requirements-zoo.lock` et `sim/requirements-llm.lock`, les noms
  que citent les protocoles. `envs/` ajoute l'en-tête et les réunit au même endroit.
- **rliable 1.2.0** n'existe qu'en archive source. pip la construit en quelques secondes (Python pur).
- **Sous Linux**, `analysis.txt` s'installe tel quel : l'intégration continue le fait sous Ubuntu
  (`.github/workflows/verify.yml`). Là, `check_numbers.py` et les tests tranchent ; les dernières
  décimales d'un bootstrap bougent avec le processeur, si bien que la comparaison octet par octet est
  exigée sous macOS arm64, la plateforme des résultats, quand Linux se contente de l'afficher.
- **Entraîner sous Linux** marche aussi avec `train.txt`, mais les essais de ce dépôt viennent de macOS
  arm64. Ailleurs, la même graine aléatoire donne d'autres courbes : MuJoCo, JAX et PyTorch arrondissent
  différemment d'un processeur à l'autre. Un nouvel essai sur une autre machine éprouve les statistiques, pas chaque courbe.
- **GRPO** a tourné sur le processeur graphique d'Apple (MPS) ou sur le processeur, selon l'essai
  (`sim/llm/LLM_PROTOCOL.md`, écart 11). `grpo.py` télécharge `Qwen/Qwen2.5-0.5B-Instruct` et
  `unsloth/Llama-3.2-1B-Instruct` depuis Hugging Face ; `docs/figures/build.py` télécharge le
  découpeur en jetons de Qwen. `grpo.py` fige la révision
  du modèle qu'ont utilisée tous les essais, la seule présente dans le cache (`sim/llm/LLM_PROTOCOL.md`, écart 15).

## La chaîne du document

Hors des environnements Python, la fabrication des PDF et des figures a employé :

| Outil | Version | Employé par |
|---|---|---|
| pandoc | 3.6.1 | `docs/build.sh` |
| md2star | 3.13.5 (PyPI) | `docs/build.sh` (le DOCX et un premier PDF) |
| TeX Live 2026 : LuaHBTeX 1.24.0, latexmk 4.88 | | `docs/build.sh` (le PDF final) |
| sprezzature-figures | 2.14.1 (2.14.0 sur PyPI) | `docs/figures/build.py`, `article/figures/build.py` |
| rsvg-convert (librsvg) | 2.61.3 | du SVG au PDF et au PNG |
| git | 2.50.0 | `make verify` |

`make check` et `make verify` n'ont besoin que d'`analysis.txt` : ces outils dessinent et composent, ils
ne calculent aucun chiffre.
