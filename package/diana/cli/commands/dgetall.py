import os
import click
from crud.cli.utils import validate_endpoint
from diana.apis import DcmDir


@click.command()
@click.argument("source", callback=validate_endpoint, type=click.STRING)
@click.option("-b", "--binary", help="Get binary file as well as data", is_flag=True, default=False)
@click.pass_context
def cli(ctx, source, binary):
    """Get all instances from DcmDir for chaining"""
    click.echo(click.style('Get All Items from DcmDir', underline=True, bold=True))

    if not ctx.obj.get("items"):
        ctx.obj["items"] = []

    if not isinstance(source, DcmDir):
        click.echo("Wrong endpoint type")

    items = []
    for root, dirs, files in os.walk(source.path):
        items.append(os.path.join(root, files))

    for item in items:
        _item = source.get(item, file=binary)
        ctx.obj["items"].append(_item)
