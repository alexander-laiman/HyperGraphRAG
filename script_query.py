import os
from hypergraphrag import HyperGraphRAG
os.environ["OPENAI_API_KEY"] = ""

rag = HyperGraphRAG(working_dir=f"expr/example")

query_text = 'What is the fate of the man in the story?'

result = rag.query(query_text)
print(result)