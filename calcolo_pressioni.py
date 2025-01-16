import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Titolo dell'app
st.title("Calcolo delle Pressioni Litostatiche")

# Caricamento file Excel
uploaded_file = st.file_uploader("Carica un file Excel con la stratigrafia", type=["xlsx"])



# Funzioni dal tuo script
def calculate_vertical_pressure(z, stratigraphy):
    pressure = 0
    for i, layer in stratigraphy.iterrows():
        top = layer['Top Level']
        bottom = layer['Bottom Level']
        gamma = layer['Unit Weight']
        if z > top:
            continue
        elif z >= bottom:
            pressure += gamma * (z - top)
            break
        else:
            pressure += gamma * (bottom - top)
    return pressure

def calculate_pore_pressure(z, water_table):
    return max(0, (water_table - z) * 10)

def calculate_effective_vertical_pressure(z, stratigraphy, water_table):
    return calculate_vertical_pressure(z, stratigraphy) - calculate_pore_pressure(z, water_table)

def plot_graphs(stratigraphy, water_table):
    quotas_ngf = [stratigraphy['Top Level'].iloc[0]] + \
                 list(stratigraphy['Bottom Level']) + [water_table]
    quotas_ngf = sorted(set(quotas_ngf))

    vertical_pressures = [calculate_vertical_pressure(z, stratigraphy) for z in quotas_ngf]
    pore_pressures = [calculate_pore_pressure(z, water_table) for z in quotas_ngf]
    effective_pressures = [vp - pp for vp, pp in zip(vertical_pressures, pore_pressures)]

    # Grafico
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(vertical_pressures, quotas_ngf, label="Pressione Litostatica", color="blue")
    ax.plot(pore_pressures, quotas_ngf, label="Pressione Falda", color="cyan")
    ax.plot(effective_pressures, quotas_ngf, label="Pressione Efficace", color="green")

    # Aggiungi rettangoli per gli strati
    max_pressure = max(vertical_pressures)
    for i, layer in stratigraphy.iterrows():
        rect_color = layer['Color']
        ax.fill_betweenx([layer['Top Level'], layer['Bottom Level']],
                         max_pressure + 10, max_pressure + 20, color=rect_color, alpha=0.5)
        ax.text(max_pressure + 15, (layer['Top Level'] + layer['Bottom Level']) / 2,
                layer['Name'], rotation=90, va='center')

    ax.axhline(y=water_table, color='red', linestyle='--', label='Falda')
    ax.invert_yaxis()
    ax.set_xlabel("Pressione [kPa]")
    ax.set_ylabel("Quota [m NGF]")
    ax.legend()
    st.pyplot(fig)



if uploaded_file:
    # Lettura dati stratigrafia
    stratigraphy = pd.read_excel(uploaded_file)
    stratigraphy['Color'] = ['#d9a066', '#a0a0a0', '#8c564b']  # Esempio colori
    st.write("Dati caricati:")
    st.dataframe(stratigraphy)

    # Input falda
    water_table = st.number_input("Quota della falda altimetrica [m NGF]:", value=30.0, step=0.1)

    # Generazione grafico
    st.write("Grafico delle pressioni:")
    plot_graphs(stratigraphy, water_table)
else:
    st.write("Carica un file Excel per iniziare.")

