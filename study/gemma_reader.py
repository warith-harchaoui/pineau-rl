"""A reader from another model family (PROTOCOL.md, deviation 33): gemma3:12b, served locally by Ollama, reads the 98
experimental papers of the main comparison on the four verdict criteria Q5, X2, X7, Y9, with an exact quote per "yes".

Order: the 98 ids (our 2018 and classical 2026, experimental, as extension_stats.py) shuffled by random.Random(2034),
so that an interrupted reading stays balanced between years. --pilot reads the first 3 into codes_gemma/pilot/ (outside
the analysis); the full run writes codes_gemma/<id>.json and skips the files already written (it can be restarted).
Input: pdftotext (no -layout) of pdf/<id>.pdf and pdf/<id>-supp.pdf, page marks "[[page N]]", the references section cut
as in falsify_no.py, truncated at 320,000 characters. Ollama: temperature 0, seed 0, num_ctx 98,304, JSON schema output.
One Ollama call per criterion (precision after the pilot, deviation 33): the paper text first, then the rule.
A malformed JSON answer is an invalid decision for its criterion only (precision of 23 November 2026).
Each "yes" quote must contain its criterion's pattern of deviation 27 and is checked with check_codes.found (threshold 0.9); a failing quote gives one retry naming the failing
criteria; still failing, the decision is "invalid" (it leaves the denominators of gemma_stats.py).
The GPU is used alone: the script waits while a GRPO training (sim/llm/grpo.py) runs.

Needs Ollama on localhost:11434 with gemma3:12b, pdftotext and the PDFs (fetch_pdfs.py).
Run from study/: nohup nice -n 19 ../sim/env-an/bin/python gemma_reader.py > logs/gemma_reader.log 2>&1 &
"""
import argparse, json, os, random, re, subprocess, sys, time, urllib.request
from check_codes import found
from samples import classic26, experimental, ours18

MODEL, URL = "gemma3:12b", "http://localhost:11434"
OPTIONS = dict(temperature=0, seed=0, num_ctx=98304)
MAX_CHARS = 320_000
CRIT = ["Q5", "X2", "X7", "Y9"]
REF = re.compile(r"^\s*(\d+\.?\s*)?(references|bibliography)\s*$", re.I | re.M)  # as falsify_no.py
AFTER = re.compile(r"^\s*(appendix|appendices|supplementary material|[A-H](\.\d*)?\s+[A-Z][a-z])", re.M)

RULE = {
    "Q5": 'Q5 - The code is linked: "yes" if the paper gives a link to code (GitHub, GitLab, Bitbucket, an anonymous mirror such as anonymous.4open.science that contains the code, or a project page that leads to code). "Available on request", "will be released", "will be made public at <URL>": "no". A link to a dataset, a benchmark or a library written by others is not the paper\'s code: "no".',
    "X2": 'X2 - An uncertainty is reported on the main results: "yes" if the main results (main table or main curves) carry a measure of spread: standard deviation, standard error, confidence interval, error bars, a shaded band on a curve, ± values. Error bars alone are enough. An uncertainty only on a secondary result: "no".',
    "X7": 'X7 - The compute used is quantified: "yes" requires at least one quantity: hours, GPU-hours, FLOP, or a number of GPUs together with a duration. The name of the hardware alone (e.g. "we use an NVIDIA A100") is "no".',
    "Y9": 'Y9 - The sensitivity to at least one hyperparameter is shown: "yes" if at least one hyperparameter of the proposed method is swept (several values tried) and the resulting performance is shown (figure, table, or a sentence with numbers). An ablation that removes or replaces a component is not a hyperparameter sweep: "no" (a variant the paper presents as a component remains an ablation). A parameter set at inference counts if the paper presents it as a hyperparameter; a condition of the environment does not count.'}
PATTERN = {  # deviation 27, verbatim: a "yes" quote must contain an occurrence of its criterion's pattern (precision after the pilot)
    "Q5": r"github|gitlab|bitbucket|anonymous\.4open|code (is |are |will be )?(publicly )?available|source code|our (code|implementation)|open[- ]source",
    "X7": r"gpu|tpu|cpu|core|hours?|days|wall[- ]?clock|compute|nvidia|v100|a100",
    "X2": r"±|\+/-|standard (deviation|error)|std|confidence interval|error bar|shaded|variance|percentile",
    "Y9": r"sensitivity|ablation|sweep|grid search|robust(ness)? to|effect of|different values of",
}
SYSTEM = "You are reading a machine-learning paper for a reproducibility survey. You decide one criterion at a time, following its rule exactly."
ASK = ("\n\nCRITERION TO DECIDE.\n{rule}\n\nGive \"value\" (\"yes\" or \"no\"), \"quote\" and \"page\". For \"yes\", the quote is the "
       "passage of the paper that justifies it, copied word for word from the paper text above (one sentence or caption, at most 40 "
       "words, no paraphrase): it is checked mechanically against the PDF. The page is the number N of the closest \"[[page N]]\" "
       "mark before the quote. For \"no\", the quote is \"absent\" and the page is null. Answer with the JSON object only.")
SCHEMA = {"type": "object", "required": ["value", "quote", "page"],
          "properties": {"value": {"type": "string", "enum": ["yes", "no"]}, "quote": {"type": "string"},
                         "page": {"type": ["integer", "null"]}}}


def cut_references(t):
    while (m := REF.search(t)):
        n = AFTER.search(t, m.end())
        t = t[:m.start()] + (t[n.start():] if n else "")
    return t


def paper_text(pid):
    out = []
    for f, tag in ((f"pdf/{pid}.pdf", "page"), (f"pdf/{pid}-supp.pdf", "supplement page")):
        if os.path.exists(f):
            t = subprocess.run(["pdftotext", "-q", "-enc", "UTF-8", f, "-"], capture_output=True, text=True).stdout
            pages = t.split("\f")
            out.append(cut_references("".join(f"\n[[{tag} {i + 1}]]\n{p}" for i, p in enumerate(pages) if p.strip())))
    t = "\n".join(out)
    return t[:MAX_CHARS], len(t) > MAX_CHARS, len(t)


def chat(messages):
    body = json.dumps(dict(model=MODEL, messages=messages, stream=False, format=SCHEMA, options=OPTIONS,
                           keep_alive="30m")).encode()
    req = urllib.request.Request(f"{URL}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3 * 3600) as r:
        return json.load(r)


def digest():
    with urllib.request.urlopen(f"{URL}/api/tags", timeout=30) as r:
        return next(m["digest"] for m in json.load(r)["models"] if m["name"] == MODEL)


def gpu_busy():
    return subprocess.run(["pgrep", "-f", "python.* [^ ]*grpo\\.py"], capture_output=True).returncode == 0


def ok(ans, k, pid):
    """A "no" is always valid; a "yes" needs its quote found in the paper and containing its criterion's pattern."""
    return ans["value"] == "no" or (bool(re.search(PATTERN[k], ans["quote"], re.I)) and found(ans["quote"], pid))


def stat(r):
    return {k: r.get(k) for k in ("prompt_eval_count", "eval_count", "total_duration")}


def read(pid, dig):
    """One call per criterion: the paper text first (the prefix Ollama keeps in cache), then the criterion's rule."""
    text, truncated, chars = paper_text(pid)
    t0, crit, raw, stats, retried = time.time(), {}, {}, {}, False
    for k in CRIT:
        messages = [dict(role="system", content=SYSTEM),
                    dict(role="user", content=f"PAPER TEXT:\n\n{text}" + ASK.format(rule=RULE[k]))]
        r1 = chat(messages)
        raw[k], stats[k] = [r1["message"]["content"]], [stat(r1)]
        try:
            ans = json.loads(r1["message"]["content"])
        except json.JSONDecodeError:  # precision of 23 November 2026: a malformed answer is an invalid decision for its criterion
            crit[k] = dict(value="no", quote="", page=None, invalid=True, malformed=True)
            continue
        if not ok(ans, k, pid):  # one retry
            retried = True
            messages += [r1["message"], dict(role="user", content=(
                "Your quote is either not found word for word in the paper, or it does not state what the criterion asks. "
                "Copy exactly from the paper text the passage that states it, or answer \"no\" if no passage supports "
                "\"yes\". Give the JSON object again."))]
            r2 = chat(messages)
            raw[k].append(r2["message"]["content"])
            stats[k].append(stat(r2))
            try:
                ans = json.loads(r2["message"]["content"])
            except json.JSONDecodeError:
                crit[k] = dict(value="no", quote="", page=None, invalid=True, malformed=True)
                continue
        crit[k] = dict(ans, invalid=not ok(ans, k, pid))
    return dict(id=pid, coder="gemma3:12b", model_digest=dig, options=OPTIONS, text_chars=chars, truncated=truncated,
                criteria=crit, retried=retried, seconds=round(time.time() - t0, 1), raw=raw, ollama=stats)


def order():
    ids = sorted(experimental(ours18) + experimental(classic26))
    random.Random(2034).shuffle(ids)
    return ids


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--pilot-dir", default="codes_gemma/pilot")
    a = ap.parse_args()
    ids = order()
    assert len(ids) == 98, len(ids)
    ids, out = (ids[:3], a.pilot_dir) if a.pilot else (ids[:a.limit], "codes_gemma")
    os.makedirs(out, exist_ok=True)
    dig = digest()
    for i, pid in enumerate(ids):
        path = f"{out}/{pid}.json"
        if os.path.exists(path):
            continue
        while gpu_busy():
            print(time.strftime("%H:%M:%S"), "GRPO training running, waiting 5 min", flush=True)
            time.sleep(300)
        try:
            rec = read(pid, dig)
        except (OSError, json.JSONDecodeError, KeyError) as e:  # Ollama down or malformed answer: logged, skipped
            print(time.strftime("%H:%M:%S"), pid, "FAILED", repr(e), flush=True)
            continue
        json.dump(rec, open(path, "w"), indent=1, ensure_ascii=False)
        print(time.strftime("%H:%M:%S"), f"{i + 1}/{len(ids)}", pid, rec["seconds"], "s",
              {k: v["value"] + ("!" if v["invalid"] else "") for k, v in rec["criteria"].items()},
              "truncated" if rec["truncated"] else "", "retried" if rec["retried"] else "", flush=True)
    sys.exit(0)
