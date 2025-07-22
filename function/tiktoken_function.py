import tiktoken
from typing import List, Dict


tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")


class TiktokenFunction:

    def estimate_tokens(text: str) -> int:
        return len(tokenizer.encode(text))

    async def split_leads_by_tokens(leads: List[Dict[str, str]], max_tokens: int) -> List[List[Dict[str, str]]]:
        batches = []
        current_batch = []
        current_tokens = 0

        for lead in leads:
            line = f"id: {lead['id']}, сообщение: {lead['message']}"
            token_count = TiktokenFunction.estimate_tokens(line)

            if current_tokens + token_count > max_tokens:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(lead)
            current_tokens += token_count

        if current_batch:
            print(f"[DEBUG] Финальный батч — {len(current_batch)} лидов, {current_tokens} токенов")
            batches.append(current_batch)

        return batches
    

    async def async_count_tokens(text: str, model: str = "gpt-4o") -> int:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        return len(tokens)