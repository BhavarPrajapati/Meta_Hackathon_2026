import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# The Scaler Hackathon requires using the OpenAI client for all LLM calls
client = OpenAI(
    api_key=os.getenv("HF_TOKEN"),
    base_url=os.getenv("MODEL_API_URL", "https://api-inference.huggingface.co/v1/")
)

class CEOAgent:
    def __init__(self, model_name="meta-llama/Llama-3-70b-instruct"):
        self.model_name = model_name

    def decide(self, state):
        """Analyze current business state and decide next move."""
        prompt = f"""
        Role: Senior CEO of a tech startup.
        Current Business State:
        {json.dumps(state, indent=2)}
        
        Available Actions:
        - hire_engineer: Cost $10k/wk, increases Product Progress.
        - hire_sales: Cost $8k/wk, increases MRR Growth.
        - marketing_push: One-time $50k cost, spikes MRR.
        - fundraise: Raise $1M cash, dilute 20% equity.
        - do_nothing: Preserve cash.

        Decision Criteria:
        1. If Cash < 2 months of Burn, you MUST Fundraise or Do Nothing.
        2. If Product < 100%, prioritize hiring Engineers.
        3. If Product > 100%, prioritize Sales and Marketing.

        Instruction: Analyze the data and return ONLY the action name from the list above.
        """
        
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=15,
            temperature=0.2
        )
        return response.choices[0].message.content.strip().lower()
