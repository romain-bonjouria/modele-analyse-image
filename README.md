# Modèle d'analyse et d'indexation d'images

Ce projet contient un modèle IA léger pour :
1. apprendre à partir d'images déjà indexées (classées par dossiers),
2. construire un index,
3. retrouver les images les plus proches d'une image requête.

## Principe

Le pipeline :
- extraction d'un embedding via `ByteHistogramEmbedder` (histogramme des octets du fichier image),
- calcul de similarité cosinus,
- retour Top-K des images les plus proches.

> Le modèle est 100% offline et sans dépendances externes, pour fonctionner même en environnement restreint.

## Structure du dataset

```text
dataset/
  chats/
    chat_1.jpg
  chiens/
    chien_1.png
```

Chaque sous-dossier = une classe.

## Utilisation

```bash
PYTHONPATH=src python -m cli \
  --dataset ./dataset \
  --query ./dataset/chats/chat_1.jpg \
  --top-k 5
```

## Fichiers principaux

- `src/image_index_model.py` : cœur du modèle (embedding + index + recherche)
- `src/cli.py` : interface CLI
- `tests/test_image_index_model.py` : tests unitaires

## Évolution possible

Quand l'environnement permet d'installer des libs IA, vous pourrez remplacer l'embedder par :
- un CNN pré-entraîné,
- CLIP,
- un index FAISS pour très grands volumes.
