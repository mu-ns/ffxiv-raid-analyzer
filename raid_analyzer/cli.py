import typer
from dotenv import load_dotenv

from raid_analyzer import auth, client

load_dotenv()
app = typer.Typer(add_completion=False)


@app.command()
def login():
    auth.login()
    token = auth.get_valid_access_token()
    user = client.GraphQLClient(token).get_current_user()
    typer.echo(f"Logged in as {user['name']}.")
