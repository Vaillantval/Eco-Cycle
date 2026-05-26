"""
Test minimal — Anthropic Managed Agent
Agent  : agent_01JtxBvYdT8G45HXAcqRnndS
Env    : env_01KcomteYtWCRWRS3f1TiK3q

Usage:
    python test_agent.py "Analyse ce déchet : bouteilles plastique PET"
    ANTHROPIC_API_KEY=sk-ant-... python test_agent.py "Bonjour"
"""

import os
import sys
import threading

import anthropic

AGENT_ID = "agent_01JtxBvYdT8G45HXAcqRnndS"
ENV_ID   = "env_01KcomteYtWCRWRS3f1TiK3q"


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Erreur : ANTHROPIC_API_KEY manquant.", file=sys.stderr)
        sys.exit(1)

    user_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Bonjour, présente-toi."

    client = anthropic.Anthropic(api_key=api_key)

    # ── 1. Créer la session ───────────────────────────────────────────────────
    print(f"Création de la session (agent={AGENT_ID})…")
    try:
        session = client.beta.sessions.create(
            agent=AGENT_ID,
            environment_id=ENV_ID,
        )
    except Exception as e:
        print(f"Erreur création session : {e}", file=sys.stderr)
        sys.exit(1)

    session_id = session.id
    print(f"Session ID : {session_id}\n")

    # ── 2. Écouter le stream dans un thread ───────────────────────────────────
    done   = threading.Event()
    error  = threading.Event()

    def stream_loop():
        try:
            stream = client.beta.sessions.events.stream(session_id)
            for event in stream:
                etype = event.type

                if etype == "agent.message":
                    for block in event.content:
                        if block.type == "text":
                            print(block.text, end="", flush=True)
                    print()

                elif etype == "session.status_idle":
                    stop = getattr(event.stop_reason, "type", "end_turn")
                    print(f"\n[Session en attente — stop_reason: {stop}]")
                    done.set()
                    return

                elif etype == "session.error":
                    err = event.error
                    print(
                        f"\n[Erreur session — {getattr(err, 'type', '?')}] "
                        f"{getattr(err, 'message', '')}",
                        file=sys.stderr,
                    )
                    error.set()
                    done.set()
                    return

                elif etype == "session.status_terminated":
                    print("\n[Session terminée]")
                    done.set()
                    return

        except Exception as e:
            print(f"\n[Exception stream] {e}", file=sys.stderr)
            error.set()
            done.set()

    t = threading.Thread(target=stream_loop, daemon=True)
    t.start()

    # ── 3. Envoyer le message utilisateur ─────────────────────────────────────
    print(f"Vous : {user_text}\n")
    print("Agent : ", end="", flush=True)
    try:
        client.beta.sessions.events.send(
            session_id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": user_text}],
            }],
        )
    except Exception as e:
        print(f"\nErreur envoi message : {e}", file=sys.stderr)
        sys.exit(1)

    # ── 4. Attendre la fin ────────────────────────────────────────────────────
    done.wait(timeout=120)
    t.join(timeout=5)

    if error.is_set():
        sys.exit(1)


if __name__ == "__main__":
    main()
