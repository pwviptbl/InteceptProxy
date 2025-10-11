#!/usr/bin/env python3
"""
Script para executar o proxy em modo headless (sem interface gráfica).
"""
import sys
import asyncio
from mitmproxy.tools.dump import DumpMaster
from mitmproxy import options

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, 'src')

from core.addon import InterceptAddon
from core.config import InterceptConfig


async def run_proxy_headless():
    """Executa o proxy em modo headless"""
    print("=" * 60)
    print("InteceptProxy - Modo Headless")
    print("=" * 60)

    # Carrega configuração
    config = InterceptConfig()
    rules = config.get_rules()

    if not rules:
        print("\n⚠️  Nenhuma regra configurada!")
        print("\nPara adicionar regras, execute a versão com interface gráfica primeiro")
        print("ou edite o arquivo 'intercept_config.json' manualmente.")
        return 1

    print(f"\n📋 Regras carregadas: {len(rules)}")
    for i, rule in enumerate(rules, 1):
        status = "✓ Ativo" if rule.get('enabled', True) else "✗ Inativo"
        print(f"  {i}. [{status}] {rule['host']}{rule['path']} -> {rule['param_name']} = {rule['param_value']}")
    print("-" * 60)

    proxy_options = options.Options(listen_host='127.0.0.1', listen_port=8080)
    master = DumpMaster(proxy_options, with_termlog=True, with_dumper=False)
    master.addons.add(InterceptAddon(config))

    print("\n🚀 Iniciando proxy na porta 8080...")
    print("Pressione Ctrl+C para parar.")
    print("=" * 60 + "\n")

    try:
        await master.run()
    except KeyboardInterrupt:
        print("\n✓ Proxy encerrado pelo usuário.")
        master.shutdown()
    except Exception as e:
        print(f"\n❌ Erro ao executar proxy: {e}")
        master.shutdown()
        return 1

    return 0


def main():
    try:
        return asyncio.run(run_proxy_headless())
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
