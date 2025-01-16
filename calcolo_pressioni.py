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

# Title of the application
st.title("Calcolo delle Pressioni nel Terreno")

# File upload for stratigraphy
data_file = st.file_uploader("Carica il file Excel della stratigrafia", type=["xlsx"])
if data_file:
    stratigraphy_df = pd.read_excel(data_file)

    # Ensure correct column names
    required_columns = ["top_level", "bottom_level", "unit_weight", "title", "k"]
    if not all(col in stratigraphy_df.columns for col in required_columns):
        st.error(f"Il file deve contenere le seguenti colonne: {', '.join(required_columns)}")
    else:
        # Convert dataframe to list of dictionaries
        stratigraphy = stratigraphy_df.to_dict(orient="records")

        # User input for water table level
        water_table = st.number_input("Inserisci la quota della falda (m NGF):", value=25.0)

        # Prepare quotas for the plot
        quotas_ngf = [layer["top_level"] for layer in stratigraphy] + [layer["bottom_level"] for layer in stratigraphy]
        quotas_ngf.append(water_table)
        quotas_ngf = sorted(set(quotas_ngf), reverse=True)

        # Calculate pressures
        lithostatic_pressures = []
        water_pressures = []
        effective_pressures = []
        horizontal_pressures = []

        for z_ngf in quotas_ngf:
            lithostatic_pressure = calculate_lithostatic_pressure(z_ngf, stratigraphy)
            water_pressure = calculate_water_pressure(z_ngf, water_table)
            effective_pressure = calculate_effective_pressure(z_ngf, stratigraphy, water_table)
            horizontal_pressure = calculate_horizontal_pressure(z_ngf, stratigraphy, water_table)

            lithostatic_pressures.append(lithostatic_pressure if lithostatic_pressure is not None else 0)
            water_pressures.append(water_pressure)
            effective_pressures.append(effective_pressure if effective_pressure is not None else 0)
            horizontal_pressures.append(horizontal_pressure if horizontal_pressure is not None else 0)

        # Plot the results
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(lithostatic_pressures, quotas_ngf, label="Pressione Litostatica", color="blue", linewidth=2)
        ax.plot(water_pressures, quotas_ngf, label="Pressione Falda", color="cyan", linestyle="--", linewidth=2)
        ax.plot(effective_pressures, quotas_ngf, label="Pressione Efficace", color="green", linestyle="-.", linewidth=2)
        ax.plot(horizontal_pressures, quotas_ngf, label="Spinta Orizzontale", color="red", linestyle=":", linewidth=2)

        # Draw water table
        ax.axhline(y=water_table, color="orange", linestyle="--", linewidth=1.5, label=f"Quota Falda ({water_table} m NGF)")

        # Add stratigraphy layers
        terrain_colors = ["#D2B48C", "#A9A9A9", "#8B4513"]
        for i, layer in enumerate(stratigraphy):
            top = layer["top_level"]
            bottom = layer["bottom_level"]
            title = layer["title"]
            color = terrain_colors[i % len(terrain_colors)]

            ax.axhline(y=bottom, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
            ax.add_patch(plt.Rectangle((0, bottom), max(lithostatic_pressures), top - bottom, 
                                        color=color, alpha=0.5, edgecolor="black"))
            ax.text(max(lithostatic_pressures) / 2, (top + bottom) / 2, title, 
                    rotation=0, horizontalalignment="center", verticalalignment="center", 
                    fontsize=10, color="black")

        ax.set_xlabel("Pressione (kPa)")
        ax.set_ylabel("Quota (m NGF)")
        ax.set_title("Pressioni Verticali ed Orizzontali nel Terreno")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.7)
        st.pyplot(fig)
