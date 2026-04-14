from pathlib import Path

import folium
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.auth import authenticate_vehicle
from src.data import CITIES, GRAPH, get_city_attractions_fallback
from src.history import build_history_table, read_history, save_history_entry
from src.llm_local import fetch_city_attractions
from src.reporting import build_pdf_report
from src.search import run_algorithm, run_all_algorithms
from src.utils import now_iso


# Coordenadas aproximadas das cidades
CITY_COORDS = {
    "Aveiro": (-8.6538, 40.6405),
    "Beja": (-7.8632, 38.0151),
    "Braga": (-8.4265, 41.5454),
    "Bragança": (-6.7567, 41.8060),
    "Castelo Branco": (-7.4909, 39.8222),
    "Coimbra": (-8.4292, 40.2033),
    "Évora": (-7.9135, 38.5710),
    "Faro": (-7.9304, 37.0194),
    "Guarda": (-7.2658, 40.5373),
    "Leiria": (-8.8070, 39.7436),
    "Lisboa": (-9.1393, 38.7223),
    "Portalegre": (-7.4312, 39.2967),
    "Porto": (-8.6291, 41.1579),
    "Santarém": (-8.6859, 39.2362),
    "Setúbal": (-8.8882, 38.5244),
    "Viana do Castelo": (-8.8345, 41.6932),
    "Vila Real": (-7.7458, 41.3006),
    "Viseu": (-7.9140, 40.6610),
}

ALGORITHM_OPTIONS = {
    "Todos": "all",
    "Custo Uniforme": "ucs",
    "Profundidade Limitada": "dls",
    "Procura Sôfrega": "greedy",
    "A*": "astar",
}

ALGORITHM_NAMES = {
    "ucs": "Custo Uniforme",
    "dls": "Profundidade Limitada",
    "greedy": "Procura Sôfrega",
    "astar": "A*",
}

ITERATION_LABELS = {
    "g": "Custo acumulado (g)",
    "h": "Heurística (h)",
    "f": "Custo total (f = g + h)",
    "depth": "Profundidade",
    "stack_size_after_pop": "Tamanho da pilha",
    "frontier_size_after_pop": "Tamanho da fronteira",
}


def draw_path_graph(path: list[str]):
    graph = nx.Graph()

    for city, neighbors in GRAPH.items():
        for neighbor, distance in neighbors.items():
            graph.add_edge(city, neighbor, weight=distance)

    pos = nx.spring_layout(graph, seed=42)
    fig, ax = plt.subplots(figsize=(10, 6))

    nx.draw_networkx_edges(graph, pos, ax=ax, alpha=0.25, width=1)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=500, node_color="lightgray")
    nx.draw_networkx_labels(graph, pos, ax=ax, font_size=8)

    if path and len(path) > 1:
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=path,
            node_size=700,
            node_color="orange",
            ax=ax,
        )
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=path_edges,
            width=3,
            edge_color="red",
            ax=ax,
        )

    ax.set_title("Grafo do caminho encontrado")
    ax.axis("off")
    return fig


def draw_portugal_path_map(path: list[str]):
    m = folium.Map(location=[39.5, -8.0], zoom_start=7, tiles="OpenStreetMap")

    for city, (lon, lat) in CITY_COORDS.items():
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            popup=city,
            tooltip=city,
            color="gray",
            fill=True,
            fill_opacity=0.7,
        ).add_to(m)

    if path:
        coords = []

        for idx, city in enumerate(path):
            if city not in CITY_COORDS:
                continue

            lon, lat = CITY_COORDS[city]
            coords.append((lat, lon))

            if idx == 0:
                color = "green"
                icon = "play"
            elif idx == len(path) - 1:
                color = "red"
                icon = "flag"
            else:
                color = "blue"
                icon = "info-sign"

            folium.Marker(
                location=[lat, lon],
                popup=city,
                tooltip=city,
                icon=folium.Icon(color=color, icon=icon),
            ).add_to(m)

        if len(coords) > 1:
            folium.PolyLine(
                locations=coords,
                color="blue",
                weight=5,
                opacity=0.8,
            ).add_to(m)

    return m


def build_iterations_dataframe(iterations: list[dict]) -> pd.DataFrame:
    rows = []

    for idx, item in enumerate(iterations, start=1):
        row = {
            "Iteração": idx,
            "Cidade expandida": item.get("expanded_city", ""),
            "Caminho": " → ".join(item.get("path", [])),
        }

        for key, value in item.items():
            if key not in {"expanded_city", "path"}:
                label = ITERATION_LABELS.get(key, key.replace("_", " ").capitalize())
                row[label] = value

        rows.append(row)

    return pd.DataFrame(rows)


st.set_page_config(page_title="Trabalho Prático Final", layout="wide")

st.title("Métodos de Procura, OCR e LLM Local")
st.caption("Aplicação para procurar caminhos entre cidades portuguesas com autenticação por matrícula")

with st.sidebar:
    st.header("Configuração")

    with st.form("search_form"):
        plate = st.text_input("Matrícula")
        uploaded = st.file_uploader("Imagem da matrícula", type=["png", "jpg", "jpeg"])

        origin = st.selectbox("Origem", CITIES, index=CITIES.index("Aveiro"))
        goal = st.selectbox("Destino", CITIES, index=CITIES.index("Faro"))

        selected_algorithm_label = st.selectbox("Algoritmo", list(ALGORITHM_OPTIONS.keys()))
        algorithm = ALGORITHM_OPTIONS[selected_algorithm_label]

        depth_limit = 10
        if selected_algorithm_label == "Profundidade Limitada":
            depth_limit = st.number_input(
                "Limite de profundidade",
                min_value=1,
                max_value=50,
                value=10,
            )

        run = st.form_submit_button("Executar")

# Configuração do modelo (muda para "llama3.1" se quiseres)
llm_model = "llama3.1"

if run:
    image_path = None
    if uploaded is not None:
        out = Path("outputs")
        out.mkdir(exist_ok=True)
        image_path = out / uploaded.name
        image_path.write_bytes(uploaded.getvalue())
if run:
    image_path = None
    if uploaded is not None:
        out = Path("outputs")
        out.mkdir(exist_ok=True)
        image_path = out / uploaded.name
        image_path.write_bytes(uploaded.getvalue())

    auth_result = authenticate_vehicle(
        plate=plate or None,
        image_path=str(image_path) if image_path else None,
    )

    st.subheader("Autenticação")

    if auth_result["authenticated"]:
        st.success("Matrícula autenticada com sucesso.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Dados do veículo")
            # Usa o que o OCR detectou ou o que foi escrito no campo
            display_plate = auth_result.get('detected_plate') or plate
            st.markdown(f"**Matrícula:** {display_plate}")
            st.markdown(f"**Veículo:** {auth_result.get('vehicle', 'N/D')}")
        with col2:
            st.markdown("### Dados do proprietário")
            st.markdown(f"**Nome:** {auth_result.get('owner', 'N/D')}")
            st.markdown(f"**Origem da leitura:** {auth_result.get('source', 'N/D')}")
            
        # --- AQUI CONTINUA O RESTO DO TEU CÓDIGO DE PROCURA ---
        results = (
            run_all_algorithms(origin, goal, depth_limit=depth_limit)
            if algorithm == "all"
            else {algorithm: run_algorithm(algorithm, origin, goal, depth_limit=depth_limit)}
        )
        
        # (Aqui metes o código que gera o PDF e as Atrações que fizemos antes)

    else:
        # Se NÃO estiver autenticado
        st.error(auth_result.get("message", "A matrícula não está registada no sistema."))
        
        # Pega na matrícula que falhou (seja do OCR ou do input manual)
        failed_plate = auth_result.get('detected_plate') or plate
        
        if failed_plate:
            with st.expander(f"📝 Registar Novo Veículo ({failed_plate})"):
                new_owner = st.text_input("Nome do Proprietário")
                new_model = st.text_input("Modelo do Veículo (ex: Tesla Model 3)")
                if st.button("Gravar Registo"):
                    if new_owner and new_model:
                        from src.auth import register_new_vehicle # Garante que a função existe
                        register_new_vehicle(failed_plate, new_owner, new_model)
                        st.success("✅ Veículo registado! Clique em 'Executar' novamente para entrar.")
                    else:
                        st.error("Preencha todos os campos.")
        
        st.stop() # Importante: pára aqui para não tentar correr algoritmos sem login


    st.subheader("Resultados de procura")

    for name, result in results.items():
        pretty_name = ALGORITHM_NAMES.get(name, name)

        with st.expander(pretty_name, expanded=True):
            st.markdown(f"**Caminho final:** {' → '.join(result['path']) if result['path'] else 'Sem caminho'}")
            st.markdown(f"**Distância final:** {result['cost']} km")
            st.markdown(f"**Nós expandidos:** {result['expanded_nodes']}")
            st.markdown(f"**Sucesso:** {'Sim' if result['success'] else 'Não'}")

            if result["path"]:
                col1, col2 = st.columns(2)

                with col1:
                    fig = draw_path_graph(result["path"])
                    st.pyplot(fig)
                    plt.close(fig)

                with col2:
                    st_folium(
                        draw_portugal_path_map(result["path"]),
                        width=700,
                        height=500,
                        returned_objects=[],
                        key=f"map_{name}_{origin}_{goal}",
                    )

            if result["iterations"]:
                st.markdown("**Iterações do algoritmo**")
                df_iterations = build_iterations_dataframe(result["iterations"])
                st.dataframe(df_iterations, use_container_width=True)

    # =========================================================================
    # --- CARREGAR ATRAÇÕES ---
    # =========================================================================
    st.session_state['last_origin'] = origin
    st.session_state['last_goal'] = goal
    
    # 1. Tenta carregar pelo LLM
    atr_origem = fetch_city_attractions(origin, model=llm_model)
    atr_destino = fetch_city_attractions(goal, model=llm_model)

    # 2. Verifica se a origem falhou ou deu "No-Name"
    if not atr_origem or (len(atr_origem) > 0 and "No-Name" in atr_origem[0].get('name', '')):
        atr_origem = get_city_attractions_fallback(origin)

    # 3. Verifica se o destino falhou ou deu "No-Name"
    if not atr_destino or (len(atr_destino) > 0 and "No-Name" in atr_destino[0].get('name', '')):
        atr_destino = get_city_attractions_fallback(goal)

    # 4. Guarda no session_state para usar no PDF e na interface
    st.session_state['atracoes_origem'] = atr_origem
    st.session_state['atracoes_destino'] = atr_destino
    # =========================================================================
    # --- GERAR HISTÓRICO E RELATÓRIO ---
    # =========================================================================
    history_entry = {
        "timestamp": now_iso(),
        "vehicle": auth_result,
        "origin": origin,
        "goal": goal,
        "algorithm": algorithm,
        "depth_limit": int(depth_limit),
        "results": results,
        "attractions": {
            "origem": st.session_state['atracoes_origem'],
            "destino": st.session_state['atracoes_destino']
        },
    }

    save_history_entry(history_entry)

    out = Path("outputs")
    out.mkdir(exist_ok=True)
    pdf_path = out / f"relatorio_{origin}_{goal}_{algorithm}.pdf"
    build_pdf_report(pdf_path, history_entry)

    st.success(f"Relatório gerado: {pdf_path}")
    st.download_button(
        "Descarregar PDF",
        pdf_path.read_bytes(),
        file_name=pdf_path.name,
        mime="application/pdf",
    )


# =====================================================================
# --- ELEMENTOS FIXOS (Aparecem sempre na página) ---
# =====================================================================

st.divider()

# --- HISTÓRICO ---
st.subheader("Histórico de pesquisas")
history = read_history()

if history:
    history_rows = build_history_table(history)
    st.dataframe(pd.DataFrame(history_rows), use_container_width=True)

    with st.expander("Ver histórico completo em formato JSON"):
        st.json(history)
else:
    st.info("Ainda não existe histórico.")

st.divider()

# --- ATRAÇÕES (No fundo da página) ---
if 'atracoes_origem' in st.session_state and 'atracoes_destino' in st.session_state:
    st.subheader("📍 Sugestões Turísticas (Última Pesquisa)")
    c_att_1, c_att_2 = st.columns(2)

    with c_att_1:
        st.markdown(f"### {st.session_state.get('last_origin', 'Origem')}")
        
        if st.session_state['atracoes_origem']:
            for atracao in st.session_state['atracoes_origem']:
                st.write(f"**{atracao.get('name', 'Atração')}**")
                st.caption(atracao.get('description', ''))
        else:
            st.warning("Não foi possível carregar atrações para esta cidade.")

    with c_att_2:
        st.markdown(f"### {st.session_state.get('last_goal', 'Destino')}")
        
        if st.session_state['atracoes_destino']:
            for atracao in st.session_state['atracoes_destino']:
                st.write(f"**{atracao.get('name', 'Atração')}**")
                st.caption(atracao.get('description', ''))
        else:
            st.warning("Não foi possível carregar atrações para esta cidade.")