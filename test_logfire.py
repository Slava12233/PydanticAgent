# This example demonstrates PydanticAI running with OpenAI!

import asyncio
import os
from pydantic_ai import Agent

async def main():
    # Set project before configuring logfire
    os.environ['LOGFIRE_PROJECT'] = 'slavalabovkin1223/newtest'
    
    # configure logfire
    import logfire
    # נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
    try:
        logfire.configure(
            token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7',
            pydantic_plugin=logfire.PydanticPlugin(record='all')
        )
    except (AttributeError, ImportError):
        # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
        logfire.configure(token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7')
    
    logfire.instrument_openai()

    agent = Agent('openai:gpt-4o')

    result = await agent.run(
        'How does pyodide let you run Python in the browser? (short answer please)'
    )

    print(f'output: {result.data}')

if __name__ == "__main__":
    asyncio.run(main()) 