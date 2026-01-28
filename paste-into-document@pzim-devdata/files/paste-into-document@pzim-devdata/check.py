#!/usr/bin/python3
import os
import sys

def main() -> None:
    if len(sys.argv) < 2:
        exit(1)
    
    directory = sys.argv[1].replace("\\ ", " ")
    files = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Le répertoire doit exister et être accessible en écriture
    if not os.path.exists(directory) or not os.access(directory, os.W_OK):
        exit(1)
    
    # Maximum un fichier accepté
    if len(files) > 1:
        exit(1)
    
    # Si un fichier est sélectionné, vérifier les permissions d'écriture
    if len(files) == 1:
        filepath = files[0].replace("\\ ", " ")
        if os.path.exists(filepath) and not os.access(filepath, os.W_OK):
            exit(1)
    
    exit(0)

if __name__ == "__main__":
    main()
