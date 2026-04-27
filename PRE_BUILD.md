# Pre-Build Checklist

Complete every item before compiling. Do not ship with any of these unresolved.

---

## Debug Mode — must be fully removed, not just disabled

- [ ] Delete `DEBUG = True` constant from `main.py`
- [ ] Remove `debug: bool = False` parameter from `DispatchPage.__init__`
- [ ] Remove `self._debug` assignment in `DispatchPage.__init__`
- [ ] Remove `_debug_bypass()` method from `ui/dispatch_page/__init__.py`
- [ ] Remove the `if debug: ... else: ...` branch in `DispatchPage.__init__`, keep only `QTimer.singleShot(0, self._check_existing_session)`
- [ ] Remove `debug=DEBUG` from `DispatchPage(...)` call in `main.py`

> Patching `DEBUG = False` to `True` in a compiled binary is trivial. The code path must not exist at all.

---

## Auth Server

- [ ] Set `AUTH_SERVER` in `security/session.py` to the production URL
- [ ] Set `AUTH_SERVER` in `security/tamper_guard.py` to the same production URL
- [ ] Verify the server is live and reachable before building
- [ ] Bundle the pinned server certificate as `assets/server.pem`

---

## Discord OAuth

- [ ] Set `DISCORD_CLIENT_ID` in `security/discord_oauth.py`
- [ ] Set `DISCORD_CLIENT_SECRET` in `security/discord_oauth.py`
- [ ] Confirm redirect URI `http://localhost:5757/callback` is registered in the Discord developer portal

---

## Tamper Guard

- [ ] Fill `EXPECTED_HASHES` in `security/tamper_guard.py` with real SHA-256 hashes of the final security files
  - Use the script comment at the top of `tamper_guard.py` to generate them
  - Run it against the exact files that will be in the build, not work-in-progress versions

---

## Code Hygiene

- [ ] No `print()` calls that expose internal state, tokens, paths, or mode names
- [ ] No leftover `# TODO`, `# DEBUG`, or `# TEMP` comments in security files
- [ ] `database/user/auth.json` is in `.gitignore` and not committed
- [ ] `auth_server/sessions.json` and `auth_server/state.json` are in `.gitignore`

---

## Final Check

Run this before compiling to catch anything missed:

```bash
grep -rn "DEBUG\|_debug_bypass\|print(" security/ ui/dispatch_page/ main.py
```

If it returns any results, stop and fix them first.
