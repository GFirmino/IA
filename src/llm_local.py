import json
import ollama
import streamlit as st

@st.cache_data(show_spinner="A consultar guia turístico local...")
def fetch_city_attractions(city_name: str, model: str = "llama3.1:8b") -> list:
    # Usamos aspas triplas para evitar erros de sintaxe com o JSON interno
    prompt = f"""
    És um guia turístico de Portugal. 
    Lista exatamente as 3 principais atrações de {city_name}.
    Responde APENAS em formato JSON puro, numa lista.
    Usa o idioma Português de Portugal.

    Exemplo do formato:
    [
      {{"name": "Nome da Atração", "description": "Descrição curta"}},
      {{"name": "Nome da Atração", "description": "Descrição curta"}},
      {{"name": "Nome da Atração", "description": "Descrição curta"}}
    ]
    """
    # Nota: No f-string, usamos {{ e }} para representar as chavetas do JSON

    try:
        response = ollama.generate(model=model, prompt=prompt, format="json")
        raw_text = response.get('response', '').strip()
        
        print(f"\n--- DEBUG LLM ({city_name}) ---")
        print(raw_text)
        print("-------------------------------\n")

        if not raw_text:
            return None

        data = json.loads(raw_text)
        temp_list = []

        # TRATAMENTO DE FORMATO (Lista vs Objeto Único)
        if isinstance(data, list):
            temp_list = data
        elif isinstance(data, dict):
            # Se o LLM mandou só um: {"name": "Barra Beach", ...}
            if "name" in data or "Name" in data:
                temp_list = [data]
            else:
                # Se mandou um dicionário de objetos: {"0": {...}, "1": {...}}
                for val in data.values():
                    if isinstance(val, dict):
                        temp_list.append(val)
                    elif isinstance(val, list):
                        temp_list.extend(val)

        # NORMALIZAÇÃO FINAL
        final_list = []
        for item in temp_list:
            if isinstance(item, dict):
                n = item.get("name") or item.get("Name") or "Atração"
                d = item.get("description") or item.get("Description") or "Local histórico."
                # Só adiciona se tiver conteúdo real
                if n != "Atração" or d != "Local histórico.":
                    final_list.append({"name": n, "description": d})
        
        # Se o modelo só deu 1, ele devolve esse 1. Se deu 3, devolve 3.
        return final_list[:3] if len(final_list) > 0 else None

    except Exception as e:
        print(f"Erro no processamento LLM: {e}")
        return None