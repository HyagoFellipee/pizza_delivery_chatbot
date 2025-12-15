#!/usr/bin/env python3
"""
Testes simples do chatbot
"""
import requests
import json

API_URL = "http://localhost:8004/api/chat"

def test(step, message, cart=None, total=0.0):
    """Testa uma mensagem"""
    payload = {
        "message": message,
        "conversation_history": [],
        "cart_items": cart or [],
        "total": total
    }

    print(f"\n{'='*60}")
    print(f"TESTE {step}: {message}")
    print(f"{'='*60}")

    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        print(f"✅ Resposta: {result['response'][:200]}...")
        print(f"🛒 Carrinho: {len(result['cart_items'])} itens")
        print(f"💰 Total: R$ {result['total']:.2f}")

        return result
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return None

print("\n🍕 TESTES SIMPLES DO CHATBOT 🍕\n")

# Teste 1: Listar cardápio
test(1, "Oi!")

# Teste 2: Preço específico
test(2, "Quanto custa a Margherita?")

# Teste 3: Adicionar 1 pizza
r3 = test(3, "Quero 1 Calabresa")

# Teste 4: Adicionar mais pizzas (com cart do teste anterior)
if r3:
    test(4, "Adiciona 2 Margherita", r3['cart_items'], r3['total'])

# Teste 5: Adicionar múltiplas de uma vez
test(5, "Quero 1 Portuguesa e 2 Bacon")

# Teste 6: Perguntar sobre o total com carrinho
cart_test = [{"name":"Calabresa","price":39.9,"quantity":1}]
test(6, "Qual o total?", cart_test, 39.9)

# Teste 7: Finalizar
cart_final = [
    {"name":"Calabresa","price":39.9,"quantity":2},
    {"name":"Margherita","price":35.9,"quantity":1}
]
test(7, "Pode fechar o pedido", cart_final, 115.7)

print("\n" + "="*60)
print("✅ TESTES FINALIZADOS")
print("="*60 + "\n")
