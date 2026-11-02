# Pre-entrega 5: Agente de Razonamiento Cíclico con Memoria Persistente

Agente autónomo desarrollado con **LangGraph**, **Python 3.12** y **Asyncio**, capaz de tomar decisiones de invocación de herramientas, gestionar reintentos/razonamiento cíclico ReAct y mantener memoria conversacional persistente mediante `SqliteSaver`.

## 🚀 Características
- **StateGraph y MessagesState**: Grafo de estados desacoplado con nodos de modelo y de herramientas (`ToolNode`), conectado con `tools_condition`.
- **Autonomía**: Selección de herramientas basada en docstrings semánticos usando `@tool`.
- **Persistencia de Estado**: Guardado asíncrono con `SqliteSaver` mediante un `thread_id`.
- **Resiliencia**: Control de límites de recursión (`recursion_limit=10`) y ejecución totalmente asíncrona.

## 🛠️ Requisitos e Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <tu-repo-url>
   cd <nombre-del-repo>
# Agente-de-razonamiento-ciclico-con-memoria-persistente
