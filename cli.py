import sys
import os
import click

# Adiciona o diretório `src` ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from core.config import InterceptConfig


@click.group()
def cli():
    """
    InteceptProxy CLI - Ferramenta de linha de comando para gerenciar
    regras de interceptação e executar o proxy.
    """
    pass


@cli.command('list')
def list_rules():
    """Lista todas as regras de interceptação configuradas."""
    config = InterceptConfig()
    rules = config.get_rules()

    if not rules:
        click.echo("Nenhuma regra configurada.")
        return

    click.echo(click.style(f"{'#':<3} {'STATUS':<8} {'HOST':<25} {'CAMINHO':<20} {'PARÂMETRO':<20} {'VALOR'}", bold=True))
    click.echo("-" * 100)

    for i, rule in enumerate(rules):
        status = "Ativo" if rule.get('enabled', True) else "Inativo"
        status_color = "green" if status == "Ativo" else "red"

        click.echo(
            f"{i+1:<3} "
            f"{click.style(status, fg=status_color):<8} "
            f"{rule['host']:<25} "
            f"{rule['path']:<20} "
            f"{rule['param_name']:<20} "
            f"{rule['param_value']}"
        )


@cli.command('add')
@click.option('--host', required=True, help="Host/domínio a ser interceptado.")
@click.option('--path', required=True, help="Caminho da rota (ex: /contato).")
@click.option('--param', 'param_name', required=True, help="Nome do parâmetro a ser modificado.")
@click.option('--value', 'param_value', required=True, help="Novo valor para o parâmetro.")
def add_rule(host, path, param_name, param_value):
    """Adiciona uma nova regra de interceptação."""
    config = InterceptConfig()
    if config.add_rule(host, path, param_name, param_value):
        click.echo(click.style("✓ Regra adicionada com sucesso!", fg="green"))
    else:
        click.echo(click.style("✗ Erro ao adicionar regra.", fg="red"))


@cli.command('remove')
@click.argument('index', type=int)
def remove_rule(index):
    """Remove uma regra pelo seu número de índice."""
    config = InterceptConfig()
    rule_index = index - 1  # Converte para índice baseado em zero

    if 0 <= rule_index < len(config.get_rules()):
        if config.remove_rule(rule_index):
            click.echo(click.style(f"✓ Regra #{index} removida com sucesso!", fg="green"))
        else:
            click.echo(click.style(f"✗ Erro ao remover regra #{index}.", fg="red"))
    else:
        click.echo(click.style(f"✗ Erro: Índice #{index} é inválido.", fg="red"))


import asyncio
from mitmproxy.tools.dump import DumpMaster
from mitmproxy import options
from core.addon import InterceptAddon
from core.logger_config import log


@cli.command('toggle')
@click.argument('index', type=int)
def toggle_rule(index):
    """Ativa ou desativa uma regra pelo seu número de índice."""
    config = InterceptConfig()
    rule_index = index - 1  # Converte para índice baseado em zero

    if 0 <= rule_index < len(config.get_rules()):
        if config.toggle_rule(rule_index):
            new_status = "Ativa" if config.get_rules()[rule_index]['enabled'] else "Inativa"
            click.echo(click.style(f"✓ Status da regra #{index} alterado para: {new_status}", fg="green"))
        else:
            click.echo(click.style(f"✗ Erro ao alterar status da regra #{index}.", fg="red"))
    else:
        click.echo(click.style(f"✗ Erro: Índice #{index} é inválido.", fg="red"))


@cli.command('run')
def run_proxy():
    """Inicia o proxy em modo headless."""
    config = InterceptConfig()
    rules = config.get_rules()

    if not rules:
        click.echo(click.style("\n⚠️ Nenhuma regra configurada. Adicione uma com 'add' primeiro.", fg="yellow"))
        return

    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("🚀 Iniciando InteceptProxy em modo headless...", bold=True, fg="cyan"))
    click.echo(click.style("=" * 60, fg="cyan"))

    log.info("Proxy (CLI) iniciando...")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_proxy_headless(config))
    except KeyboardInterrupt:
        click.echo("\n✓ Proxy encerrado pelo usuário.")
        log.info("Proxy (CLI) encerrado pelo usuário.")
    except Exception as e:
        click.echo(click.style(f"\n❌ Erro ao executar proxy: {e}", fg="red"))
        log.error(f"Erro ao executar proxy (CLI): {e}", exc_info=True)


async def start_proxy_headless(config):
    """Função assíncrona para iniciar o mitmdump."""
    proxy_options = options.Options(listen_host='127.0.0.1', listen_port=8080)
    master = DumpMaster(proxy_options, with_termlog=True, with_dumper=False)
    master.addons.add(InterceptAddon(config))

    click.echo(click.style("\nProxy escutando em http://127.0.0.1:8080", fg="green"))
    click.echo("Pressione Ctrl+C para parar.")

    await master.run()


if __name__ == "__main__":
    cli()
