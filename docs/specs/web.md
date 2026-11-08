# Design: `turtle-web` — moved

The turtle-web dashboard spec now lives with the code it describes, in the turtle-web repository:
**[turtle-web/docs/specs/web.md](https://github.com/jaaknt/turtle-web/blob/main/docs/specs/web.md)**.

It moved on 2026-11-08, after Step 6. The history up to then is in this repository's
`git log -- docs/specs/web.md`.

What still lives here, in turtle-backtest:

- **Step 0, the `turtle_web` read-only role:** `db/init.sh` for fresh installs, and
  [implementation.md](../implementation.md) §"Add the `turtle_web` role to an existing database".
- **The tables it reads**, `turtle.signal` among them: [persist-signal.md](persist-signal.md).
