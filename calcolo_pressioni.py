import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def calculate_lithostatic_pressure(z_ngf, stratigraphy):
    pressure = 0
    in_stratum = False

    for i, layer in enumerate(stratigraphy):
        top = layer["top_level"]
        bottom = layer["bottom_level"]
        gamma = layer["unit_weight"]

        if top >= z_ngf >= bottom:
            in_stratum = True
            for j in range(i):
                thickness = stratigraphy[j]["top_level"] - stratigraphy[j]["bottom_level"]
                pressure += stratigraphy[j]["unit_weight"] * thickness
            thickness_in_layer = top - z_ngf
            pressure += gamma * thickness_in_layer
            break

    if not in_stratum:
        return None

    return pressure

def calculate_water_pressure(z_ngf, water_table):
    return max(0, (water_table - z_ngf) * 10)

def calculate_effective_pressure(z_ngf, stratigraphy, water_table):
    lithostatic_pressure = calculate_lithostatic_pressure(z_ngf, stratigraphy)
    water_pressure = calculate_water_pressure(z_ngf, water_table)

    if lithostatic_pressure is not None:
        return lithostatic_pressure - water_pressure
    else:
        return None

def calculate_horizontal_pressure(z_ngf, stratigraphy, water_table):
    effective_pressure = calculate_effective_pressure(z_ngf, stratigraphy, water_table)
    water_pressure = calculate_water_pressure(z_ngf, water_table)

    for i, layer in enumerate(stratigraphy):
        top = layer["top_level"]
        bottom = layer["bottom_level"]
        k = layer["k"]

        if top >= z_ngf >= bottom or (z_ngf == top and i > 0):
            if z_ngf == top and i > 0:
                k = stratigraphy[i - 1]["k"]
            if effective_pressure is not None:
                return k * effective_pressure + water_pressure
            else:
                return None

    return None

st.title("Calcolo delle Pressioni nel Terreno")

uploaded_file = st.file_uploader("Carica il file Excel della stratigrafia", type="xlsx")
water_table = st.number_input("Inserisci la quota della falda (m NGF):", value=25.0, step=0.1)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        stratigraphy = df.to_dict(orient="records")

        # Preparare le quote per il grafico
        quotas_ngf = [stratigraphy[0]["top_level"], water_table]  # Quota di sommità e falda
        
        for i, layer in enumerate(stratigraphy[:-1]):  # Per gli strati intermedi
            quotas_ngf.append(layer["bottom_level"])  # Quota di fondo
            quotas_ngf.append(layer["bottom_level"] - 0.01)  # 1 cm sotto il cambio di strato
            quotas_ngf.append(stratigraphy[-1]["bottom_level"])  # Quota di fondo dell'ultimo strato

        quotas_ngf = sorted(set(quotas_ngf), reverse=True)  # Rimuovi duplicati e ordina decrescente
        
        # Calcolo dei valori
        data = {
            "Quota (m NGF)": quotas_ngf,
            "Pressione Litostatica (kPa)": [],
            "Pressione Falda (kPa)": [],
            "Pressione Efficace (kPa)": [],
            "Spinta Orizzontale (kPa)": []
        }

        for z_ngf in quotas_ngf:
            lithostatic_pressure = calculate_lithostatic_pressure(z_ngf, stratigraphy)
            water_pressure = calculate_water_pressure(z_ngf, water_table)
            effective_pressure = calculate_effective_pressure(z_ngf, stratigraphy, water_table)
            horizontal_pressure = calculate_horizontal_pressure(z_ngf, stratigraphy, water_table)

            data["Pressione Litostatica (kPa)"].append(lithostatic_pressure if lithostatic_pressure is not None else 0)
            data["Pressione Falda (kPa)"].append(water_pressure)
            data["Pressione Efficace (kPa)"].append(effective_pressure if effective_pressure is not None else 0)
            data["Spinta Orizzontale (kPa)"].append(horizontal_pressure if horizontal_pressure is not None else 0)

        # Convertire i dati in un DataFrame per la tabella
        results_df = pd.DataFrame(data)

        # Visualizzare la tabella
        st.subheader("Tabella dei Risultati")
        st.dataframe(results_df)

        # Plot dei valori
        st.subheader("Grafico delle Pressioni")
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(data["Pressione Litostatica (kPa)"], quotas_ngf, label="Pressione Litostatica", color="blue", linewidth=2)
        ax.plot(data["Pressione Falda (kPa)"], quotas_ngf, label="Pressione Falda", color="cyan", linestyle="--", linewidth=2)
        ax.plot(data["Pressione Efficace (kPa)"], quotas_ngf, label="Pressione Efficace", color="green", linestyle="-.", linewidth=2)
        ax.plot(data["Spinta Orizzontale (kPa)"], quotas_ngf, label="Spinta Orizzontale", color="red", linestyle=":", linewidth=2)
        
        ax.axhline(y=water_table, color="orange", linestyle="--", linewidth=1.5, label=f"Quota Falda ({water_table} m NGF)")   
        
        ax.set_xlabel("Pressione (kPa)")
        ax.set_ylabel("Quota (m NGF)")
        ax.set_title("Pressioni Verticali ed Orizzontali nel Terreno")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.7)
        st.pyplot(fig)

        # Rettangoli colorati per rappresentare gli strati di terreno
        terrain_colors = ["#D2B48C", "#A9A9A9", "#8B4513"]  # Marroncino chiaro, grigio, marrone scuro

        for i, layer in enumerate(stratigraphy):
            top = layer["top_level"]
            bottom = layer["bottom_level"]
            title = layer["title"]
            color = terrain_colors[i % len(terrain_colors)]  # Ciclo sui colori se gli strati sono più di 3

        # Rettangolo colorato per lo strato
        plt.gca().add_patch(plt.Rectangle(
            (0, bottom),                  # Coordinate in basso a sinistra del rettangolo
            max(lithostatic_pressure),   # Larghezza del rettangolo
            top - bottom,                 # Altezza del rettangolo
            color=color,                  # Colore di sfondo
            alpha=0.5,                    # Trasparenza
            edgecolor="black"             # Colore del bordo
        ))

        # Testo del titolo dello strato, centrato nel rettangolo
        plt.text(
            max(lithostatic_pressure) / 2,  # Posizione orizzontale del testo (centro del grafico)
            (top + bottom) / 2,             # Posizione verticale del testo (centro dello strato)
            title,                          # Titolo dello strato
            rotation=0,                     # Nessuna rotazione del testo
            horizontalalignment="center",   # Allineamento orizzontale centrato
            verticalalignment="center",     # Allineamento verticale centrato
            fontsize=10,                    # Dimensione del font
            color="black"                   # Colore del testo
        )

    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
