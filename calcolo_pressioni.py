import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Titolo dell'app
st.title("Calcolo delle Pressioni Litostatiche")


# Input dei dati della stratigrafia con i titoli degli strati
stratigraphy = [
    {"top_level": 35, "bottom_level": 28, "unit_weight": 18, "k": 0.5, "title": "Remblais"},
    {"top_level": 28, "bottom_level": 20, "unit_weight": 20, "k": 0.45, "title": "Marnes"},
    {"top_level": 20, "bottom_level": 12, "unit_weight": 21, "k": 0.3, "title": "Alluvions"},
]

# Quota della falda in metri NGF
water_table = 26  # Quota della falda

# Funzioni di calcolo (rimangono invariate)
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
    if z_ngf >= water_table:
        return 0
    else:
        return 10 * (water_table - z_ngf)

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

# Preparare le quote per il grafico
quotas_ngf = [stratigraphy[0]["top_level"], water_table]  # Quota di sommità e falda
for i, layer in enumerate(stratigraphy[:-1]):  # Per gli strati intermedi
    quotas_ngf.append(layer["bottom_level"])  # Quota di fondo
    quotas_ngf.append(layer["bottom_level"] - 0.01)  # 1 cm sotto il cambio di strato
quotas_ngf.append(stratigraphy[-1]["bottom_level"])  # Quota di fondo dell'ultimo strato

quotas_ngf = sorted(set(quotas_ngf), reverse=True)  # Rimuovi duplicati e ordina decrescente

# Calcolo dei valori per il grafico
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

# Plot dei valori
plt.figure(figsize=(12, 8))

# Plot pressione litostatica
plt.plot(lithostatic_pressures, quotas_ngf, label="Pressione Litostatica", color="blue", linewidth=2)

# Plot pressione della falda
plt.plot(water_pressures, quotas_ngf, label="Pressione Falda", color="cyan", linestyle="--", linewidth=2)

# Plot pressione efficace
plt.plot(effective_pressures, quotas_ngf, label="Pressione Efficace", color="green", linestyle="-.", linewidth=2)

# Plot spinta orizzontale
plt.plot(horizontal_pressures, quotas_ngf, label="Spinta Orizzontale", color="red", linestyle=":", linewidth=2)

# Linea della falda
plt.axhline(y=water_table, color="orange", linestyle="--", linewidth=1.5, label="Quota Falda ({} m NGF)".format(water_table))

# Linee e rettangoli per gli strati con il nome del terreno
terrain_colors = ["#D2B48C", "#A9A9A9", "#8B4513"]  # Marroncino chiaro, grigio, marrone scuro

for i, layer in enumerate(stratigraphy):
    top = layer["top_level"]
    bottom = layer["bottom_level"]
    title = layer["title"]
    color = terrain_colors[i % len(terrain_colors)]  # Ciclo sui colori

    # Linea orizzontale per il cambio di strato
    plt.axhline(y=bottom, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)

    # Rettangolo colorato per rappresentare lo strato, con il nome del terreno
    plt.gca().add_patch(plt.Rectangle((0, bottom), max(lithostatic_pressures), top - bottom,
                                       color=color, alpha=0.5))

    # Testo del titolo dello strato, centrato nel rettangolo
    plt.text(max(lithostatic_pressures) / 2, (top + bottom) / 2, title,
             rotation=0, horizontalalignment="center", verticalalignment="center",
             fontsize=10, color="black")

# Configurazioni grafiche
plt.xlabel("Pressione (kPa)")
plt.ylabel("Quota (m NGF)")
plt.title("Pressioni Verticali ed Orizzontali nel Terreno")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.7)

# Mostrare il grafico
plt.tight_layout()
plt.show()
