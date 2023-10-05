def get_bot_token():
    # Read the bot token from the token.txt file using a raw string literal
    with open(r"C:\bots\medSQL\config\token.txt", "r") as token_file:
        return token_file.read().strip()
