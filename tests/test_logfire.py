# This example demonstrates PydanticAI running with OpenAI!

import asyncio
import os
import sys

# הוספת תיקיית הפרויקט ל-PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.core.config import LOGFIRE_API_KEY, LOGFIRE_PROJECT
from pydantic_ai import Agent

async def main():
    # Set project before configuring logfire
    os.environ['LOGFIRE_PROJECT'] = LOGFIRE_PROJECT
    
    # configure logfire
    import logfire
    # נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
    try:
        logfire.configure(
            token=LOGFIRE_API_KEY,
            pydantic_plugin=logfire.PydanticPlugin(record='all')
        )
    except (AttributeError, ImportError):
        # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
        logfire.configure(token=LOGFIRE_API_KEY)
    
    logfire.instrument_openai()

    agent = Agent('openai:gpt-4o')

    result = await agent.run(
        'How does pyodide let you run Python in the browser? (short answer please)'
    )

    print(f'output: {result.data}')

if __name__ == "__main__":
    asyncio.run(main()) 