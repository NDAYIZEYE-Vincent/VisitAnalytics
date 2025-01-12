from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import os

# Dictionnaires pour les choix dans les formulaires
niveau_instruction = {
    'sans_instruction': 'Sans instruction',
    'Primaire': 'Niveau Primaire',
    'secondaire': 'Niveau secondaire',
    'universitaire': 'Niveau universitaire'
}

état_matrimonial = {
    'Célibataire': 'Célibataire',
    'Marié(e)': 'Marié(e)',
    'Divorcé(e)': 'Divorcé(e)',
    'Veuf(ve)': 'Veuf(ve)'
}

motif_entre = {
    'Études et Recherche': 'Éducation',
    'Réseautage social': 'Navigation Internet',
    'Accès à Internet': 'Communication',
    'Accès Logiciels': 'Accès logiciels',
    'Impression et Scanner': 'Impression',
    'Travaux_numeriques': 'Travaux numériques',
    'Jeux_en_ligne': 'Jeux en ligne',
    'Autre': 'Autre'
}

# Page d'identification
page_identification = ui.nav_panel(
    "Identification",
    ui.page_sidebar(
        ui.sidebar(
            ui.h3("Identification du participant"),
            ui.input_text("nom", "Nom du participant"),
            ui.input_select('sex', "Sexe", choices=['Masculin', 'Feminin']),
            ui.input_select('état', "État matrimonial", choices=list(état_matrimonial.keys())),
            ui.input_select('Niveau', "Niveau d'instruction", choices=list(niveau_instruction.keys())),
            ui.input_numeric('Numero', 'Numéro de téléphone', value=0),
            ui.input_numeric("age", "Âge", value=0),
            ui.input_text("commune", "Commune"),
            ui.input_text("province", "Province"),
            ui.input_select("motif", 'Motif de visite', choices=list(motif_entre.keys())),
            ui.output_ui("autre_motif_ui"),
            ui.row(
                ui.column(6, ui.input_action_button('submit', 'Soumettre', class_="btn btn-primary")),
                ui.column(6, ui.input_action_button('annuler', 'Annuler', class_="btn btn-secondary"))
            ),
            ui.output_text_verbatim('message')
        ),
        ui.card(
            ui.h3("Données enregistrées"),
            ui.output_data_frame("tableau_donnees")
        )
    )
)

# Page de graphiques avec matplotlib
page_graphiques = ui.nav_panel(
    "Graphiques",
    ui.h1('Analyse des visiteurs'),
    ui.layout_columns(
        ui.card(
            ui.h3("Répartition par sexe"),
            ui.output_plot("graphique_sexe", height='400px')
        ),
        ui.card(
            ui.h3("Répartition par niveau d'instruction"),
            ui.output_plot("graphique_niveau_instruction", height='400px')
        )
    ),
    ui.layout_columns(
        ui.card(
            ui.h3("Répartition par province"),
            ui.output_plot("graphique_provinces", height='400px')
        ),
        ui.card(
            ui.h3("Répartition par motif"),
            ui.output_plot("graphique_motifs", height='400px')
        )
    )
)

# Interface utilisateur principale
app_ui = ui.page_navbar(
    page_identification,
    page_graphiques,
    title="Gestion des Participants",
    bg="#0062cc",
    inverse=True,
)

def server(input, output, session):
    # Configuration du fichier CSV et des variables réactives
    CSV_FILE_PATH = 'participants_data.csv'
    mode_edition = reactive.Value(False)
    ligne_edition = reactive.Value(None)
    message_status = reactive.Value("")
    
    # Fonction pour charger les données existantes
    def load_existing_data():
        try:
            if os.path.exists(CSV_FILE_PATH):
                return pd.read_csv(CSV_FILE_PATH, encoding='utf-8')
            else:
                return pd.DataFrame(columns=[
                    'Nom', 'Sexe', 'État matrimonial', 'Niveau d\'instruction',
                    'Numéro de téléphone', 'Âge', 'Commune', 'Province', 'Motif'
                ])
        except Exception as e:
            print(f"Erreur de chargement du CSV: {e}")
            return pd.DataFrame()
    
    donnees_stockees = reactive.Value(load_existing_data())
    
    # Fonction pour réinitialiser le formulaire
    def reset_form():
        ui.update_text("nom", value="")
        ui.update_select("sex", selected="Masculin")
        ui.update_select("état", selected="Célibataire")
        ui.update_select("Niveau", selected="sans_instruction")
        ui.update_numeric("Numero", value=0)
        ui.update_numeric("age", value=0)
        ui.update_text("commune", value="")
        ui.update_text("province", value="")
        ui.update_select("motif", selected="Études et Recherche")
        if hasattr(input, 'autre_motif'):
            ui.update_text("autre_motif", value="")
        mode_edition.set(False)
        ligne_edition.set(None)
        message_status.set("")

    # Gestion du champ "autre motif"
    @render.ui
    def autre_motif_ui():
        if input.motif() == 'Autre':
            return ui.input_text("autre_motif", "Précisez le motif")
        return None

    # Gestion de la soumission du formulaire
    @reactive.effect
    @reactive.event(input.submit)
    def handle_submit():
        if not input.nom():
            message_status.set("Le nom est obligatoire")
            return
        
        motif_final = input.autre_motif() if input.motif() == 'Autre' else motif_entre.get(input.motif(), input.motif())
        
        donnees = {
            'Nom': input.nom(),
            'Sexe': input.sex(),
            'État matrimonial': état_matrimonial.get(input.état(), input.état()),
            'Niveau d\'instruction': niveau_instruction.get(input.Niveau(), input.Niveau()),
            'Numéro de téléphone': input.Numero(),
            'Âge': input.age(),
            'Commune': input.commune(),
            'Province': input.province(),
            'Motif': motif_final
        }
        
        df = donnees_stockees.get().copy()
        
        try:
            if mode_edition():
                idx = ligne_edition()
                for col, valeur in donnees.items():
                    df.loc[idx, col] = valeur
                message_status.set("Modification effectuée avec succès")
            else:
                df = pd.concat([df, pd.DataFrame([donnees])], ignore_index=True)
                message_status.set("Nouvelle entrée ajoutée avec succès")
            
            df.to_csv(CSV_FILE_PATH, index=False, encoding='utf-8')
            donnees_stockees.set(df)
            reset_form()
            
        except Exception as e:
            message_status.set(f"Erreur lors de la sauvegarde: {str(e)}")
            print(f"Erreur lors de la sauvegarde: {e}")

    # Affichage des messages d'état
    @render.text
    def message():
        return message_status.get()
    
    # Affichage du tableau de données
    @output
    @render.data_frame
    def tableau_donnees():
        df = donnees_stockees.get()
        
        if not df.empty:
            df_display = df.copy()
            df_display['Actions'] = df_display.index.map(lambda i: ui.HTML(f"""
                <div class="btn-group">
                    <button 
                        id="delete_{i}" 
                        class="btn btn-danger btn-sm" 
                        onclick="Shiny.setInputValue('delete_row', {i}, {{priority: 'event'}})">
                        🗑
                    </button>
                    <button 
                        id="update_{i}" 
                        class="btn btn-primary btn-sm" 
                        onclick="Shiny.setInputValue('update_row', {i}, {{priority: 'event'}})">
                        ✏
                    </button>
                </div>
            """))
            return df_display
        return df

    # Gestion de la suppression d'une ligne
    @reactive.effect
    @reactive.event(input.delete_row)
    def delete_row():
        if input.delete_row() is not None:
            df = donnees_stockees.get().copy()
            df = df.drop(input.delete_row()).reset_index(drop=True)
            try:
                df.to_csv(CSV_FILE_PATH, index=False, encoding='utf-8')
                donnees_stockees.set(df)
                message_status.set("Suppression effectuée avec succès")
            except Exception as e:
                message_status.set(f"Erreur lors de la suppression: {str(e)}")
                print(f"Erreur lors de la sauvegarde du fichier CSV: {e}")

    # Gestion de la modification d'une ligne
    @reactive.effect
    @reactive.event(input.update_row)
    def handle_update_row():
        if input.update_row() is not None:
            idx = input.update_row()
            df = donnees_stockees.get()
            if idx < len(df):
                row = df.iloc[idx]
                
                ui.update_text("nom", value=str(row['Nom']))
                ui.update_select("sex", selected=str(row['Sexe']))
                
                état_key = next(
                    (k for k, v in état_matrimonial.items() if v == row['État matrimonial']),
                    list(état_matrimonial.keys())[0]
                )
                ui.update_select("état", selected=état_key)
                
                niveau_key = next(
                    (k for k, v in niveau_instruction.items() if v == row["Niveau d'instruction"]),
                    list(niveau_instruction.keys())[0]
                )
                ui.update_select("Niveau", selected=niveau_key)
                
                ui.update_numeric("Numero", value=int(row['Numéro de téléphone']))
                ui.update_numeric("age", value=int(row['Âge']))
                ui.update_text("commune", value=str(row['Commune']))
                ui.update_text("province", value=str(row['Province']))
                
                motif_key = next(
                    (k for k, v in motif_entre.items() if v == row['Motif']),
                    'Autre'
                )
                ui.update_select("motif", selected=motif_key)
                
                if motif_key == 'Autre':
                    ui.update_text("autre_motif", value=str(row['Motif']))
                
                mode_edition.set(True)
                ligne_edition.set(idx)
                message_status.set("Mode édition activé")

    # Gestion de l'annulation
    @reactive.effect
    @reactive.event(input.annuler)
    def handle_cancel():
        reset_form()
        message_status.set("Formulaire réinitialisé")

    # Création des graphiques avec matplotlib
    @render.plot
    def graphique_sexe():
        df = donnees_stockees.get()
        if not df.empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            counts = df['Sexe'].value_counts()
            ax.pie(counts, labels=counts.index, autopct='%1.1f%%')
            ax.set_title('Répartition par sexe')
            plt.close()  # Fermer la figure précédente
            return fig

    @render.plot
    def graphique_niveau_instruction():
        df = donnees_stockees.get()
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            counts = df['Niveau d\'instruction'].value_counts()
            counts.plot(kind='bar', ax=ax)
            ax.set_title("Répartition par niveau d'instruction")
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            plt.close()  # Fermer la figure précédente
            return fig

    @render.plot
    def graphique_provinces():
        df = donnees_stockees.get()
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            counts = df['Province'].value_counts()
            counts.plot(kind='bar', ax=ax)
            ax.set_title('Répartition par province')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            plt.close()  # Fermer la figure précédente
            return fig

    @render.plot
    def graphique_motifs():
        df = donnees_stockees.get()
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            counts = df['Motif'].value_counts()
            counts.plot(kind='bar', ax=ax)
            ax.set_title('Répartition par motif')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            plt.close()  # Fermer la figure précédente
            return fig

app = App(app_ui, server)