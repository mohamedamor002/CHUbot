"""
Évaluation du CHUbot — métriques calculées via Ollama (sans dépendance OpenAI).

Métriques :
  - faithfulness      : la réponse se base-t-elle uniquement sur le contexte ? (0-1)
  - answer_correctness: la réponse est-elle correcte vs la vérité terrain ?   (0-1)
  - context_relevance : le contexte récupéré est-il pertinent pour la question ?(0-1)

Usage :
    python tests/evaluate.py --limit 10
    python tests/evaluate.py --cat Remuneration
    python tests/evaluate.py           # 105 questions complètes
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ── Prompts d'évaluation ─────────────────────────────────────────────────────

_FAITHFULNESS_PROMPT = """Tu es un évaluateur. Réponds UNIQUEMENT par un nombre entre 0 et 1.

Contexte récupéré :
{context}

Réponse du chatbot :
{answer}

La réponse est-elle entièrement basée sur le contexte fourni, sans informations inventées ?
1.0 = entièrement basée sur le contexte
0.5 = partiellement basée
0.0 = inventée / hors contexte

Réponds uniquement par un nombre (ex: 0.8) :"""

_CORRECTNESS_PROMPT = """Tu es un évaluateur. Réponds UNIQUEMENT par un nombre entre 0 et 1.

Question : {question}
Réponse correcte (vérité terrain) : {ground_truth}
Réponse du chatbot : {answer}

La réponse du chatbot est-elle factuellement correcte par rapport à la vérité terrain ?
1.0 = entièrement correcte
0.5 = partiellement correcte
0.0 = incorrecte ou hors sujet

Réponds uniquement par un nombre (ex: 0.7) :"""

_CONTEXT_RELEVANCE_PROMPT = """Tu es un évaluateur. Réponds UNIQUEMENT par un nombre entre 0 et 1.

Question : {question}
Contexte récupéré :
{context}

Le contexte récupéré contient-il les informations nécessaires pour répondre à la question ?
1.0 = contexte très pertinent et suffisant
0.5 = contexte partiellement pertinent
0.0 = contexte hors sujet ou vide

Réponds uniquement par un nombre (ex: 0.9) :"""


# ── LLM évaluateur ───────────────────────────────────────────────────────────

_eval_llm = None

def _get_eval_llm():
    global _eval_llm
    if _eval_llm is None:
        from langchain_ollama import ChatOllama
        from bot.config.settings import settings
        auth = settings.ollama_auth_headers
        _eval_llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            client_kwargs={"headers": auth} if auth else {},
            temperature=0.0,
            num_predict=10,  # on veut juste un nombre
        )
    return _eval_llm


async def _score(prompt: str) -> float:
    """Appelle le LLM et extrait un score flottant entre 0 et 1."""
    import re
    try:
        llm = _get_eval_llm()
        msg = await llm.ainvoke(prompt)
        text = (msg.content or "").strip()
        match = re.search(r"([\d]+\.?[\d]*)", text)
        if match:
            val = float(match.group(1))
            return max(0.0, min(1.0, val))
    except Exception as e:
        print(f"         ⚠ Score erreur : {e}")
    return 0.0


# ── Collecte des réponses CHUbot ─────────────────────────────────────────────

async def _build_samples(questions: list) -> list:
    from bot.retrieval.chain import ask
    from bot.retrieval.preprocessor import preprocess_query
    from bot.retrieval.chain import _search, _format_context

    samples = []
    total = len(questions)

    for i, qr in enumerate(questions, 1):
        question = qr["question"]
        print(f"  [{i:3d}/{total}] {question[:70]}...")

        try:
            enriched, dept = await preprocess_query(question)
            docs = await _search(enriched, dept)
            context = _format_context(docs) if docs else ""
            answer = await ask(question)
        except Exception as e:
            print(f"         ⚠ Erreur CHUbot : {e}")
            context = ""
            answer = ""

        samples.append({
            "id":           qr.get("id", ""),
            "categorie":    qr.get("categorie", ""),
            "question":     question,
            "answer":       answer,
            "context":      context,
            "ground_truth": qr["reponse"],
        })

    return samples


# ── Calcul des métriques ──────────────────────────────────────────────────────

async def _evaluate_samples(samples: list) -> list:
    total = len(samples)
    print(f"\nCalcul des métriques ({total} questions × 3 métriques)...\n")

    for i, s in enumerate(samples, 1):
        print(f"  Évaluation [{i}/{total}] {s['question'][:50]}...")

        ctx_short = s["context"][:1500] if s["context"] else "(aucun contexte)"

        s["faithfulness"]       = await _score(_FAITHFULNESS_PROMPT.format(
            context=ctx_short, answer=s["answer"]))
        s["answer_correctness"] = await _score(_CORRECTNESS_PROMPT.format(
            question=s["question"], ground_truth=s["ground_truth"], answer=s["answer"]))
        s["context_relevance"]  = await _score(_CONTEXT_RELEVANCE_PROMPT.format(
            question=s["question"], context=ctx_short))

        print(f"    faithfulness={s['faithfulness']:.2f}  "
              f"correctness={s['answer_correctness']:.2f}  "
              f"ctx_relevance={s['context_relevance']:.2f}")

    return samples


# ── Sauvegarde & résumé ───────────────────────────────────────────────────────

def _save_and_print(samples: list, output_path: Path):
    import csv
    from datetime import datetime

    metric_keys = ["faithfulness", "answer_correctness", "context_relevance"]

    def _fallback_path(path: Path) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return path.with_name(f"{path.stem}-{stamp}{path.suffix}")

    # CSV détaillé
    csv_path = output_path / "results.csv"
    fieldnames = ["id", "categorie", "question", "answer", "ground_truth",
                  "faithfulness", "answer_correctness", "context_relevance"]
    try:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in samples:
                writer.writerow({k: s.get(k, "") for k in fieldnames})
    except PermissionError:
        csv_path = _fallback_path(csv_path)
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in samples:
                writer.writerow({k: s.get(k, "") for k in fieldnames})
    print(f"\nRésultats CSV → {csv_path}")

    # JSON détaillé
    json_path = output_path / "results.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
    except PermissionError:
        json_path = _fallback_path(json_path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
    print(f"Résultats JSON → {json_path}")

    # Résumé console
    print("\n" + "═" * 55)
    print("  SCORES GLOBAUX")
    print("═" * 55)
    for key in metric_keys:
        vals = [s[key] for s in samples if isinstance(s.get(key), float)]
        avg = sum(vals) / len(vals) if vals else 0.0
        bar = "█" * int(avg * 20)
        print(f"  {key:<30} {avg:.3f}  {bar}")

    # Par catégorie
    from collections import defaultdict
    by_cat = defaultdict(lambda: defaultdict(list))
    for s in samples:
        cat = s.get("categorie", "Autre")
        for key in metric_keys:
            if isinstance(s.get(key), float):
                by_cat[cat][key].append(s[key])

    print("\n" + "─" * 55)
    print("  SCORES PAR CATÉGORIE")
    print("─" * 55)
    for cat, metrics in sorted(by_cat.items()):
        avgs = {k: sum(v)/len(v) for k, v in metrics.items() if v}
        scores = "  ".join(f"{k[:5]}={v:.2f}" for k, v in avgs.items())
        print(f"  {cat:<30} {scores}")
    print("═" * 55)


# ── Point d'entrée ────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",  type=int, default=None)
    parser.add_argument("--cat",    type=str, default=None)
    parser.add_argument("--output", type=str, default="data/eval")
    parser.add_argument("--ragas", action="store_true", help="Run RAGAS evaluation using the local embedder")
    args = parser.parse_args()

    with open(ROOT / "data" / "eval" / "dataset.json", encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions_reponses"]
    if args.cat:
        questions = [q for q in questions if args.cat.lower() in q.get("categorie","").lower()]
        print(f"Filtre '{args.cat}' → {len(questions)} questions")
    if args.limit:
        questions = questions[:args.limit]

    print(f"\nÉvaluation de {len(questions)} questions sur le CHUbot...\n")

    samples = await _build_samples(questions)
    samples = await _evaluate_samples(samples)

    output_path = ROOT / args.output
    output_path.mkdir(parents=True, exist_ok=True)
    _save_and_print(samples, output_path)

    return samples, args


# ── Évaluation RAGAS (synchrone, hors boucle asyncio) ────────────────────────

def _run_ragas(samples: list, args) -> None:
    print("\nCalcul des métriques RAGAS en cours...")
    try:
        from bot.config.settings import settings
        from ragas import evaluate
        from ragas.dataset_schema import EvaluationDataset
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ragas.metrics import faithfulness, answer_correctness, context_precision
        from langchain_ollama import OllamaEmbeddings

        try:
            emb = OllamaEmbeddings(
                model=settings.EMBEDDING_MODEL,
                base_url=settings.EMBEDDING_BASE_URL,
            )
        except Exception as e:
            print(f"  ⚠ Embedder local non disponible ({e}) — RAGAS ignoré.")
            return

        ds_items = []
        for s in samples:
            retrieved = s.get("context") or ""
            ds_items.append({
                "user_input":        s.get("question", ""),
                "retrieved_contexts": [retrieved],
                "response":          s.get("answer", ""),
                "reference":         s.get("ground_truth", ""),
            })

        ds = EvaluationDataset.from_list(ds_items)

        metrics = [faithfulness, answer_correctness, context_precision]
        result = evaluate(
            dataset=ds,
            metrics=metrics,
            llm=_get_eval_llm(),
            embeddings=emb,
            raise_exceptions=False,
            allow_nest_asyncio=False,
        )
        print("RAGAS result:\n", result)
    except Exception as e:
        print(f"  ⚠ Erreur durant RAGAS evaluation : {e}")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _result = None
    try:
        _result = loop.run_until_complete(main())
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        asyncio.set_event_loop(None)
        loop.close()

    if _result is not None:
        _samples, _args = _result
        if _args.ragas:
            _run_ragas(_samples, _args)
