import argparse
from localdeamon.deamon import Deamon
from localdeamon.console import console
from rich.panel import Panel
from rich.markdown import Markdown
from localdeamon.spell import spell
from localdeamon.prompt import Prompt
from localdeamon.llm import get_llm
from localdeamon.context import Context
from localdeamon import console as c

@spell
def understand(task: str) -> str:
    prompt = Prompt.load("UNDERSTAND")
    ctx = Context.fromPrompt(prompt, task=task)
    resp = get_llm().invoke(ctx.messages)

    c.task_output(resp.content)
    c.divider()

    return resp.content

@spell
def summon_deamon(task: str) -> str:
    ctx = Context()
    ctx.add_user_message(task)
    deamon = Deamon()

    return deamon.run(ctx)

def main():
    parser = argparse.ArgumentParser(description='Local Daemon - Minimalistic LLM agent framework')
    parser.add_argument('task', nargs='?', help='Task for the agent to perform')
    parser.add_argument('--no-understand', action='store_true', help='Skip the UNDERSTAND phase')

    args = parser.parse_args()

    if not args.task:
        parser.print_help()
        return

    if args.no_understand:
        resp = summon_deamon(args.task)
    else:
        pipeline = understand | summon_deamon
        resp = pipeline(args.task)

    console.print(Panel(Markdown(resp), title="[bold green]Final Response[/bold green]", border_style="green", padding=(1, 2)))

if __name__ == '__main__':
    main()