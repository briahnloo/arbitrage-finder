<!-- e94fba25-694e-49d6-b7e5-ff5989b9754d 80457326-0537-4bab-9bc6-61ea47fca9cd -->
# Fix Discord Bot 401 / Improper Token Error

### Step 1: Confirm where the token comes from

1. Open `discord_bot.py` and verify how the token is loaded (it uses `load_dotenv()` and `ArbitrageBotConfig.DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')`).
2. Confirm which `.env` file is being read (project root vs `discord/` directory) and which working directory is used when running `python discord_bot.py`.

### Step 2: Verify the DISCORD_BOT_TOKEN value

1. In the Discord Developer Portal, go to your application → Bot → Reset/Copy **Bot Token**.
2. Ensure you are not copying a client secret, client ID, or user token—only the bot token from the Bot tab.
3. Paste this token (exactly) into the `.env` file entry `DISCORD_BOT_TOKEN=...` used by `discord_bot.py`.
4. Make sure the `.env` file is not committed or truncated and has no extra quotes or spaces around the token.

### Step 3: Ensure the environment file is actually loaded

1. Run the bot with a command that uses the project root as the working directory (so `load_dotenv()` finds the correct `.env`).
2. If needed, temporarily add a debug print or log to show the first few characters of `ArbitrageBotConfig.DISCORD_TOKEN` (without exposing the full token) to confirm it is non-empty and matches the bot you created.
3. If the value is `None` or empty, adjust the `.env` location or call `load_dotenv(dotenv_path=...)` with the explicit path.

### Step 4: Check for common token issues

1. If you regenerated the token in the Developer Portal, confirm that the old token is not still being used anywhere (restart shells, terminals, and processes).
2. Ensure you are not mixing test and production Discord apps; the token must match the app you invited to the server.
3. Confirm there are no hidden characters in the token line (e.g., copied newline, backticks) by retyping if in doubt.

### Step 5: Re-run and validate

1. Restart the bot process and confirm the log no longer shows `GET ... /users/@me ... 401` or `Improper token has been passed`.
2. Verify that `on_ready` fires and the bot appears online in your Discord server.
3. Test a simple slash command (e.g., `/help`) to ensure the bot is fully functional.

### Step 6: Clean up and harden

1. Remove any temporary debug logging of token contents once things work.
2. Ensure `.env` is listed in `.gitignore` and that no token is present in any committed file.
3. Optionally document the bot setup and environment requirements in `README.md` for future reference.

### To-dos

- [ ] Inspect `discord_bot.py` to confirm how and where DISCORD_BOT_TOKEN is loaded (load_dotenv, config class, working directory).
- [ ] In Discord Developer Portal, copy the correct Bot token and update the DISCORD_BOT_TOKEN entry in the active .env file.
- [ ] Confirm the .env file is being loaded when running the bot and that DISCORD_BOT_TOKEN is non-empty and from the right app.
- [ ] Restart the bot, confirm 401/Improper token errors are gone, and test a slash command in Discord.
- [ ] Remove any debug token logs, ensure .env is ignored by git, and note setup steps in README.md.