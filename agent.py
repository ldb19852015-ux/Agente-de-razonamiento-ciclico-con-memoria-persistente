import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

# ==============================================================================
# FASE 1: CONTRATO DE HERRAMIENTAS (@tool) - Altamente descriptivas
# ==============================================================================

@tool
async def buscar_pedidos(cliente_id: int) -> str:
    """Busca en la base de datos transaccional los pedidos históricos, 
    la cantidad total de compras y el monto acumulado para un cliente específico.
    
    Args:
        cliente_id (int): El identificador único numérico del cliente (ej. 102 o 105).
    """
    base_datos = {
        102: {
            "cliente_id": 102,
            "pedidos": 3,
            "total": 14500,
            "ultimo_pedido": "2026-10-10",
            "detalle": "Equipamiento de red y conectividad FTTH/HFC"
        },
        105: {
            "cliente_id": 105,
            "pedidos": 1,
            "total": 3200,
            "ultimo_pedido": "2026-10-22",
            "detalle": "Mantenimiento preventivo de rectificador"
        }
    }
    
    if cliente_id in base_datos:
        return json.dumps(base_datos[cliente_id], ensure_ascii=False)
    else:
        return json.dumps({"error": f"Cliente {cliente_id} no encontrado en la base de datos."}, ensure_ascii=False)


@tool
async def consultar_inventario_tecnico(codigo_item: str) -> str:
    """Consulta el stock físico y la ubicación de los componentes de infraestructura y red en el depósito central.
    
    Args:
        codigo_item (str): El código alfanumérico del componente técnico (ej. 'MODEM-HFC-01').
    """
    inventario = {
        "MODEM-HFC-01": {"codigo": "MODEM-HFC-01", "stock": 45, "ubicacion": "Depósito Central Paclín"},
        "RECTIFICADOR-48V": {"codigo": "RECTIFICADOR-48V", "stock": 12, "ubicacion": "Depósito Catamarca Capital"}
    }
    
    if codigo_item in inventario:
        return json.dumps(inventario[codigo_item], ensure_ascii=False)
    return json.dumps({"error": f"Item {codigo_item} sin stock o no registrado."}, ensure_ascii=False)


tools = [buscar_pedidos, consultar_inventario_tecnico]


# ==============================================================================
# FASE 2 Y 3: GRAFO (MessagesState) Y PERSISTENCIA (AsyncSqliteSaver)
# ==============================================================================

async def main():
    print("\n" + "=" * 65)
    print("🤖 AGENTE REACT DE RAZONAMIENTO CÍCLICO CON MEMORIA PERSISTENTE")
    print("=" * 65)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ No se encontró OPENAI_API_KEY en las variables de entorno.")

    # Configuración del LLM
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, api_key=api_key)
    model_with_tools = model.bind_tools(tools)

    # Nodo del agente (Razonador autónomo)
    async def call_model(state: MessagesState):
        messages = state["messages"]
        response = await model_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # Definición del StateGraph
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    db_path = "checkpoint.sqlite"

    # Persistencia asíncrona con SqliteSaver
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)

        config = {
            "configurable": {"thread_id": "sesion_auditoria_tecnica_01"},
            "recursion_limit": 10  # Previene bucles infinitos requerido por consigna
        }

        # PRUEBA MULTI-PASO (Fuerza al agente a invocar MÚLTIPLES herramientas en un mismo ciclo)
        pregunta_multi = (
            "Necesito una auditoría rápida: por un lado, consultame cuántos pedidos tuvo el cliente 102 "
            "y por el otro, verificame el stock disponible del item MODEM-HFC-01."
        )
        print(f"\n💬 USUARIO (Consulta multi-paso / multi-herramienta):\n{pregunta_multi}\n")

        async for event in graph.astream({"messages": [("user", pregunta_multi)]}, config, stream_mode="values"):
            mensaje_actual = event["messages"][-1]
            mensaje_actual.pretty_print()

        # PRUEBA DE MEMORIA PERSISTENTE (Mismo thread_id recuperando contexto previo)
        pregunta_memoria = "¿Y qué cliente tuvo mayor cantidad de pedidos según lo que acabamos de revisar?"
        print(f"\n💬 USUARIO (Evaluación de memoria con thread_id):\n{pregunta_memoria}\n")

        async for event in graph.astream({"messages": [("user", pregunta_memoria)]}, config, stream_mode="values"):
            mensaje_actual = event["messages"][-1]
            mensaje_actual.pretty_print()

    print("\n" + "=" * 65)
    print("✅ PRUEBA COMPLETADA CON ÉXITO")
    print("=" * 65)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())