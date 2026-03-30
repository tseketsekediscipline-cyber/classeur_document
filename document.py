import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import messagebox 
import json
import matplotlib.pyplot as plt


# 1. On définit le dossier à ranger (met le chemin d'un dossier de test ici)
dossier_a_trier = "./mon_bordel"

# 2. On crée le dossier s'il n'existe pas encore pour notre test
if not os.path.exists(dossier_a_trier):
    os.makedirs(dossier_a_trier)
    print(f"Dossier {dossier_a_trier} créé. Mets des fichiers dedans !")

def charger_config():
    nom_fichier = "config.json"
    if os.path.exists(nom_fichier):
        with open(nom_fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Si le fichier est perdu, on garde une petite base pour que ça marche
        return {".pdf": "Documents_PDF", ".txt": "Documents_Texte"}

# On charge la config au démarrage
config = charger_config()

def initialiser_bdd():
    # Crée le fichier 'gestion_fichiers.db' s'il n'existe pas
    connexion = sqlite3.connect("gestion_fichiers.db")
    curseur = connexion.cursor()
    
    # On crée une table pour stocker les infos
    curseur.execute('''
        CREATE TABLE IF NOT EXISTS fichiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            extension TEXT,
            destination TEXT,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    connexion.commit()
    connexion.close()

def enregistrer_dans_bdd(nom, ext, dest):
    connexion = sqlite3.connect("gestion_fichiers.db")
    curseur = connexion.cursor()
    
    # On insère les données dans les colonnes correspondantes
    curseur.execute('''
        INSERT INTO fichiers (nom, extension, destination)
        VALUES (?, ?, ?)
    ''', (nom, ext, dest))
    
    connexion.commit()
    connexion.close()

def ranger():
    for nom_fichier in os.listdir(dossier_a_trier):
        chemin_source = os.path.join(dossier_a_trier, nom_fichier)
        
        if os.path.isfile(chemin_source):
            extension = os.path.splitext(nom_fichier)[1].lower()
            
            if extension in config:
                nom_dossier_dest = config[extension]
                dossier_dest_complet = os.path.join(dossier_a_trier, nom_dossier_dest)
                
                if not os.path.exists(dossier_dest_complet):
                    os.makedirs(dossier_dest_complet)

                # --- GESTION DES DOUBLONS ---
                chemin_final = os.path.join(dossier_dest_complet, nom_fichier)
                nom_final = nom_fichier
                compteur = 1
                
                # Si un fichier avec le même nom existe déjà, on change le nom
                while os.path.exists(chemin_final):
                    nom_pur = os.path.splitext(nom_fichier)[0]
                    nom_final = f"{nom_pur}_{compteur}{extension}"
                    chemin_final = os.path.join(dossier_dest_complet, nom_final)
                    compteur += 1

                try:
                    # On déplace avec le nom final (peut-être renommé)
                    shutil.move(chemin_source, chemin_final)
                    
                    # On enregistre dans la BDD
                    enregistrer_dans_bdd(nom_final, extension, nom_dossier_dest)
                    print(f"Succès : {nom_final} rangé dans {nom_dossier_dest}")
                except Exception as e:
                    print(f"Erreur lors du déplacement de {nom_fichier} : {e}")


def chercher_par_extension():
    ext_cherchee = input("Quelle extension voulez-vous voir ? (ex: .jpg) : ").lower()
    
    connexion = sqlite3.connect("gestion_fichiers.db")
    curseur = connexion.cursor()
    
    # Le '?' est une sécurité pour éviter les piratages (injections SQL)
    curseur.execute("SELECT * FROM fichiers WHERE extension = ?", (ext_cherchee,))
    resultats = curseur.fetchall()
    
    if not resultats:
        print(f"Aucun fichier avec l'extension {ext_cherchee} n'a été trouvé.")
    else:
        print(f"\n--- RÉSULTATS POUR {ext_cherchee} ---")
        for ligne in resultats:
            print(f"ID: {ligne[0]} | Nom: {ligne[1]} | Chemin: {ligne[3]}")
            
    connexion.close()

def nettoyer_bdd():
    connexion = sqlite3.connect("gestion_fichiers.db")
    curseur = connexion.cursor()
    
    # On récupère tous les fichiers pour vérifier leur existence
    curseur.execute("SELECT id, nom, destination FROM fichiers")
    tous_les_fichiers = curseur.fetchall()
    
    compteur_suppression = 0
    
    for f in tous_les_fichiers:
        id_db, nom, dossier = f
        # On recrée le chemin pour voir si le fichier est là
        chemin_reel = os.path.join(dossier_a_trier, dossier, nom)
        
        if not os.path.exists(chemin_reel):
            # Si le fichier n'existe plus, on le supprime de la base
            curseur.execute("DELETE FROM fichiers WHERE id = ?", (id_db,))
            compteur_suppression += 1
            print(f"Nettoyage : {nom} n'existe plus, supprimé de la base.")
            
    connexion.commit()
    connexion.close()
    print(f"Fin du nettoyage. {compteur_suppression} entrées supprimées.")

def afficher_fichiers():
    connexion = sqlite3.connect("gestion_fichiers.db")
    curseur = connexion.cursor()
    
    # On récupère tout l'historique
    curseur.execute("SELECT * FROM fichiers")
    resultats = curseur.fetchall()
    
    if not resultats:
        print("\n[!] La base de données est vide pour le moment.")
    else:
        print("\n--- HISTORIQUE DES FICHIERS RANGÉS ---")
        for ligne in resultats:
            # ligne[0]=ID, ligne[1]=Nom, ligne[3]=Dossier destination
            print(f"ID: {ligne[0]} | Nom: {ligne[1]} | Destination: {ligne[3]}")
            
    connexion.close()

def afficher_stats():
    # 1. Connexion à la base pour récupérer les données
    connexion = sqlite3.connect("gestion_fichiers.db")
    curseur = connexion.cursor()
    
    # On compte combien de fichiers il y a par dossier (destination)
    curseur.execute("SELECT destination, COUNT(*) FROM fichiers GROUP BY destination")
    resultats = curseur.fetchall()
    connexion.close()

    if not resultats:
        messagebox.showwarning("Stats", "La base de données est vide !")
        return

    # 2. Préparation des données pour le graphique
    noms_dossiers = [ligne[0] for ligne in resultats]
    nombres_fichiers = [ligne[1] for ligne in resultats]

    # 3. Création du graphique avec Matplotlib
    plt.figure(figsize=(10, 6))
    plt.bar(noms_dossiers, nombres_fichiers, color='#89b4fa') # Une jolie couleur bleue
    plt.title("Répartition de tes documents par catégorie", fontsize=14)
    plt.xlabel("Dossiers de destination")
    plt.ylabel("Nombre de fichiers")
    plt.xticks(rotation=45) # Incliner les noms pour qu'ils soient lisibles
    plt.tight_layout()
    
    # Affiche la fenêtre avec le graphique
    plt.show()


def lancer_gui():
    fenetre = tk.Tk()
    fenetre.title("StudyOrganizer Pro")
    fenetre.geometry("700x750")
    fenetre.configure(bg="#1e1e2e") # Fond sombre moderne

    # --- STYLE ---
    style_titre = {"font": ("Segoe UI", 20, "bold"), "bg": "#1e1e2e", "fg": "#cdd6f4"}
    style_label = {"font": ("Segoe UI", 10), "bg": "#1e1e2e", "fg": "#a6adc8"}
    style_btn_primary = {"font": ("Segoe UI", 11, "bold"), "bg": "#89b4fa", "fg": "#1e1e2e", "relief": "flat", "activebackground": "#b4befe"}

    # --- 1. HEADER ---
    tk.Label(fenetre, text="📂 StudyOrganizer Pro", **style_titre).pack(pady=30)

    # --- 2. BARRE DE RECHERCHE DESIGN ---
    search_frame = tk.Frame(fenetre, bg="#1e1e2e")
    search_frame.pack(pady=10)
    
    tk.Label(search_frame, text="Rechercher une extension :", **style_label).pack(side=tk.LEFT, padx=5)
    entree_recherche = tk.Entry(search_frame, font=("Segoe UI", 11), bg="#313244", fg="white", insertbackground="white", borderwidth=0)
    entree_recherche.pack(side=tk.LEFT, padx=10, ipady=3) # ipady pour agrandir la zone de saisie

    # --- 3. LISTE DES FICHIERS (PLUS LARGE ET PROPRE) ---
    list_frame = tk.Frame(fenetre, bg="#313244", padx=10, pady=10)
    list_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)

    scroll = tk.Scrollbar(list_frame)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    liste_visuelle = tk.Listbox(list_frame, font=("Consolas", 10), bg="#313244", fg="#f5e0dc", 
                                borderwidth=0, highlightthickness=0, selectbackground="#45475a",
                                yscrollcommand=scroll.set)
    liste_visuelle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.config(command=liste_visuelle.yview)

 # --- ÉTAPE A : On crée la fonction qui ouvre le fichier ---
    def ouvrir_fichier_au_double_clic(event):
        try:
            selection = liste_visuelle.get(liste_visuelle.curselection())
            parties = selection.split(" ⮕ ")
            nom_f = parties[0].strip()
            dossier_d = parties[1].strip()
            
            # On construit le chemin et on le transforme en chemin "absolu" 
            chemin_relatif = os.path.join(dossier_a_trier, dossier_d, nom_f)
            chemin_absolu = os.path.abspath(chemin_relatif)
            
            # On vérifie si le fichier existe vraiment avant d'essayer
            if os.path.exists(chemin_absolu):
                print(f"Ouverture de : {chemin_absolu}")
                os.system(f'open "{chemin_absolu}"')
            else:
                print(f"Erreur : Le fichier n'existe pas à l'adresse {chemin_absolu}")
        except Exception as e:
            print(f"Erreur : {e}")


    # Cette ligne est CRUCIALE : elle fait le lien entre ton clic et l'ouverture
    liste_visuelle.bind('<Double-1>', ouvrir_fichier_au_double_clic)

    # --- ÉTAPE C : Ta fonction rafraichir (on la garde mais on s'assure du format) ---
    def rafraichir(filtre=None):
        liste_visuelle.delete(0, tk.END)
        connexion = sqlite3.connect("gestion_fichiers.db")
        curseur = connexion.cursor()
        if filtre:
            curseur.execute("SELECT nom, destination FROM fichiers WHERE extension = ?", (filtre,))
        else:
            curseur.execute("SELECT nom, destination FROM fichiers")
        for f in curseur.fetchall():
            # IMPORTANT : On utilise le signe ⮕ pour que l'Étape A puisse le couper
            liste_visuelle.insert(tk.END, f"{f[0].ljust(40)} ⮕ {f[1]}")
        connexion.close()

    def action_ranger():
        ranger()
        rafraichir()
        messagebox.showinfo("OK", "Tes cours sont rangés !")

    # --- 4. BOUTONS STYLISÉS ---
    tk.Button(search_frame, text="Rechercher", command=lambda: rafraichir(entree_recherche.get().lower()), 
              bg="#f5c2e7", relief="flat", cursor="hand2").pack(side=tk.LEFT)

    tk.Button(fenetre, text=" RANGER LES DOCUMENTS", command=action_ranger, 
              **style_btn_primary, width=30, cursor="hand2").pack(pady=10)

    tk.Button(fenetre, text=" SYNCHRONISER LA BASE", command=lambda: [nettoyer_bdd(), rafraichir()], 
              bg="#fab387", relief="flat", width=25, cursor="hand2").pack(pady=5)
    
    tk.Button(fenetre, text=" VOIR MON ANALYSE BUSINESS", command=afficher_stats, 
              bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 11, "bold"), 
              width=30, cursor="hand2").pack(pady=10)
    
    tk.Button(fenetre, text="QUITTER", command=fenetre.quit, bg="#1e1e2e", fg="#f38ba8", 
              borderwidth=0, cursor="hand2").pack(pady=20)

    rafraichir()
    fenetre.mainloop()


if __name__ == "__main__":
    initialiser_bdd() # On prépare toujours la BDD en premier
    lancer_gui()      # Et on lance l'interface !