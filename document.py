import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import messagebox 


# 1. On définit le dossier à ranger (met le chemin d'un dossier de test ici)
dossier_a_trier = "./mon_bordel"

# 2. On crée le dossier s'il n'existe pas encore pour notre test
if not os.path.exists(dossier_a_trier):
    os.makedirs(dossier_a_trier)
    print(f"Dossier {dossier_a_trier} créé. Mets des fichiers dedans !")

# 3. Dictionnaire pour associer les extensions aux dossiers
config = {
    # --- DOCUMENTS DE COURS ---
    ".pdf": "Documents_PDF",
    ".docx": "Documents_Word",
    ".doc": "Documents_Word",
    ".txt": "Documents_Texte",
    ".pptx": "Presentations",
    ".ppt": "Presentations",
    ".xlsx": "Tableaux_Excel",
    ".xls": "Tableaux_Excel",
    ".csv": "Donnees_Recherche",

    # --- IMAGES ET GRAPHES ---
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".svg": "Images_Vectorielles",
    ".bmp": "Images",

    # --- VIDÉOS ET AUDIO (POUR LES ENREGISTREMENTS) ---
    ".mp4": "Videos",
    ".mov": "Videos",
    ".avi": "Videos",
    ".mp3": "Audio_Enregistrements",
    ".wav": "Audio_Enregistrements",

    # --- ARCHIVES (RENDUS DE PROJET) ---
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar.gz": "Archives",

    # --- CODE (SI TU FAIS DE L'INFO) ---
    ".py": "Code_Python",
    ".html": "Code_Web",
    ".css": "Code_Web",
    ".js": "Code_Web"
}

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

    # --- FONCTIONS (LES MÊMES QUE PRÉCÉDEMMENT) ---
    def rafraichir(filtre=None):
        liste_visuelle.delete(0, tk.END)
        connexion = sqlite3.connect("gestion_fichiers.db")
        curseur = connexion.cursor()
        if filtre:
            curseur.execute("SELECT nom, destination FROM fichiers WHERE extension = ?", (filtre,))
        else:
            curseur.execute("SELECT nom, destination FROM fichiers")
        for f in curseur.fetchall():
            liste_visuelle.insert(tk.END, f"  {f[0].ljust(40)} ⮕  {f[1]}")
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

    tk.Button(fenetre, text=" Synchroniser la base", command=lambda: [nettoyer_bdd(), rafraichir()], 
              bg="#fab387", relief="flat", width=25, cursor="hand2").pack(pady=5)

    tk.Button(fenetre, text="Quitter", command=fenetre.quit, bg="#1e1e2e", fg="#f38ba8", 
              borderwidth=0, cursor="hand2").pack(pady=20)

    rafraichir()
    fenetre.mainloop()
 

if __name__ == "__main__":
    initialiser_bdd() # On prépare toujours la BDD en premier
    lancer_gui()      # Et on lance l'interface !