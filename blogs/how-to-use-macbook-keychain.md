# How to Store Secrets in the Mac Keychain (and Use Them Like Environment Variables)

I used to keep API keys in `.env` because it was fast. Then I caught myself grepping my home folder for something unrelated and watching paths scroll past that file, or almost committing a backup copy. None of that is catastrophic every time, but it’s a bad habit. On a Mac you already have a place meant for secrets: **Keychain**.

This isn’t a pitch for a fancy secrets vault. It’s about the **security** tool that ships with macOS—handy for **local dev** tokens, DB URLs, signing keys, that sort of thing.

One thing to get straight up front: Keychain doesn’t literally store “environment variables.” It stores **items** (usually generic passwords) keyed by **service name** and **account**. You **pull the value out** with `security` and **`export`** it when you need it. Day to day it behaves like env vars; under the hood it’s a lookup, not a magic `.env` replacement.

You’ll need a Mac, a terminal, and if you want secrets to load automatically, willingness to touch `~/.zshrc` or similar.

## Save and read a secret

**Add** a generic password (Terminal may ask for Keychain permission the first time):

```bash
security add-generic-password \
  -a "$USER" \
  -s "myapp-dev-api-key" \
  -w "sk_live_xxxxxxxx"
```

- **`-a`** — account; often your macOS username or an app name.
- **`-s`** — service string; this is the **handle** you’ll use later. Make it unique, e.g. `myapp-dev-api-key`.
- **`-w`** — the secret. The problem is anything after `-w` can land in **shell history** (see below).

**Read** it (prints to stdout):

```bash
security find-generic-password -s "myapp-dev-api-key" -w
```

**Use it as an env var** for this shell only:

```bash
export MYAPP_API_KEY="$(security find-generic-password -s "myapp-dev-api-key" -w)"
```

After that, anything that reads `MYAPP_API_KEY` behaves as if you’d sourced a `.env`—except the value never had to live in a plaintext file on disk.

## Avoiding shell history when you add the secret

Apple’s own usage text says bluntly that **`-p` / `-w` on the command line is insecure**. Two patterns that actually work:

**Built-in prompt (often the nicest):** put **`-w` last and omit the value**. `security` will prompt for the password; that path doesn’t shove the secret into your history the way `-w "secret"` does.

```bash
security add-generic-password -a "$USER" -s "myapp-dev-api-key" -w
```

(When it asks, type or paste the secret; it’s the usual “no echo” style prompt.)

**Shell-side prompt** if you prefer to stay in bash/zsh:

```bash
printf 'Paste secret (hidden): '
read -rs SECRET
echo
security add-generic-password -a "$USER" -s "myapp-dev-api-key" -w "$SECRET"
unset SECRET
```

**Keychain Access** still counts: **File → New Password Item…** and line up the fields with whatever you pass as `-a` / `-s` so `find-generic-password` can find the item later.

## Wiring it into how you actually work

**Every new terminal** (Zsh snippet in `~/.zshrc`):

```bash
export MYAPP_API_KEY="$(security find-generic-password -s "myapp-dev-api-key" -w 2>/dev/null)"
```

`2>/dev/null` just keeps noise down if the item doesn’t exist yet.

**Per project**, a small `scripts/load-secrets.sh` that exports what that repo needs is reasonable—**don’t commit values**; document the **service names** in the README so someone else can add their own copy to Keychain.

**One shot:**

```bash
MYAPP_API_KEY="$(security find-generic-password -s "myapp-dev-api-key" -w)" uv run python -m myapp
```

## What you gain, what you’re signing up for

You lose the plaintext secret sitting in `.env` (and in a lot of accidental greps and backups). It’s **built in**, no extra install, and Keychain can **nudge or block** access per app if you tune **Access Control** on the item. For “this laptop only” dev keys, that’s often plenty.

The flip side is boring but real: **Linux and Windows** won’t help you here—those teammates need 1Password CLI, Doppler, SOPS, cloud IAM, whatever your team standard is. There’s **no automatic team sync**; new machine usually means re-adding items (iCloud Keychain exists but that’s a deliberate trust choice). If you **echo** secrets or log them, you’ve undone the point. **CI** wants provider-native secrets, not interactive Keychain. Onboarding is also slightly worse than “copy `.env.example`”—people need the **exact service strings** and commands written down somewhere.

I still reach for this for **solo Mac dev** and small personal projects where I want fewer sensitive files lying around. For **shared, audited, rotated** secrets at work, use the thing your platform team points you at.

---

So: you store with `security`, load with `export` and `$(security find-generic-password … -w)`, and you get env-var ergonomics without a plaintext `.env` for that value. The cost is **macOS-only**, a bit more **documentation**, and **discipline** around history and logging.