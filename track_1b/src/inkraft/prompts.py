"""Prompts for the examinee conditions. Versioned: change the text, bump the id."""

# v2: names Swiss federal law. Without it, the pilot on draft v0 answered for Germany, France or
# Italy. closed_plain keeps the bare question, so the effect of the context stays measurable.
PROMPT_VERSION = "inkraft-exam-v2"

DATED_SYSTEM = {
    "de": "Heute ist der 1. Oktober 2026. Die Fragen betreffen das Schweizer Bundesrecht. "
    "Antworte kurz. Wenn du dir nicht sicher bist, sag es.",
    "fr": "Nous sommes le 1er octobre 2026. Les questions portent sur le droit fédéral suisse. "
    "Réponds brièvement. Si tu n'es pas sûr, dis-le.",
    "it": "Oggi è il 1° ottobre 2026. Le domande riguardano il diritto federale svizzero. "
    "Rispondi brevemente. Se non sei sicuro, dillo.",
}
SWISS_SYSTEM = {
    "de": "Die Fragen betreffen das Schweizer Bundesrecht. "
    "Antworte kurz. Wenn du dir nicht sicher bist, sag es.",
    "fr": "Les questions portent sur le droit fédéral suisse. "
    "Réponds brièvement. Si tu n'es pas sûr, dis-le.",
    "it": "Le domande riguardano il diritto federale svizzero. "
    "Rispondi brevemente. Se non sei sicuro, dillo.",
}
SOURCE_LABEL = {"de": "Gesetzestext", "fr": "Texte de loi", "it": "Testo di legge"}
QUESTION_LABEL = {"de": "Frage", "fr": "Question", "it": "Domanda"}

CONDITIONS = {
    "closed_dated": "dated system prompt, question only (main condition)",
    "closed_swiss": "swiss federal law system prompt without date, question only",
    "closed_plain": "question only, no system prompt (SimpleQA style)",
    "open_book": "dated system prompt plus the cited paragraph of the act",
    "thinking": "closed_dated with the model's reasoning mode enabled",
}


def messages(item, condition):
    l2 = item["lang"][:2]
    q = item["question"]
    if condition == "closed_plain":
        return [{"role": "user", "content": q}]
    if condition == "closed_swiss":
        return [
            {"role": "system", "content": SWISS_SYSTEM[l2]},
            {"role": "user", "content": q},
        ]
    if condition == "open_book":
        src = item["source"]["quote"]
        user = f"{SOURCE_LABEL[l2]}:\n{src}\n\n{QUESTION_LABEL[l2]}: {q}"
        return [
            {"role": "system", "content": DATED_SYSTEM[l2]},
            {"role": "user", "content": user},
        ]
    if condition in ("closed_dated", "thinking"):
        return [
            {"role": "system", "content": DATED_SYSTEM[l2]},
            {"role": "user", "content": q},
        ]
    raise ValueError(f"unknown condition {condition}")


def extra_params(condition):
    if condition == "thinking":
        return {"chat_template_kwargs": {"enable_thinking": True}, "max_tokens": 3000}
    return {"chat_template_kwargs": {"enable_thinking": False}}


def split_reasoning(content):
    """Apertus returns its reasoning inline as <|inner_prefix|>...<|inner_suffix|>answer."""
    if content and "<|inner_suffix|>" in content:
        reasoning, answer = content.split("<|inner_suffix|>", 1)
        return answer.strip(), reasoning.replace("<|inner_prefix|>", "").strip()
    if content and "<|inner_prefix|>" in content:
        return None, content.replace("<|inner_prefix|>", "").strip()
    return content, None
