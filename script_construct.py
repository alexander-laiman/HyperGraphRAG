import os
import json
import time
from hypergraphrag import HyperGraphRAG

os.environ["OPENAI_API_KEY"] = ""

rag = HyperGraphRAG(working_dir=f"expr/example")

preferred_story = "Story"

# Load the structured book data
with open("Book_structured.json", "r", encoding="utf-8") as f:
    book_data = json.load(f)

def chunk_text(text, chunk_size=5000):
    """Split text into smaller chunks to avoid rate limits."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        if current_size + len(word) + 1 > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Extract story content and chunk it
all_chunks = []
for section in book_data["sections"]:
    if section["type"] == "story":
        story_title = section["title"]
        content = section["content"]
        
        # TEST: Just parse preferred story from collection
        if story_title != preferred_story:
            continue
            
        # Add story title as context
        full_content = f"Title: {story_title}\n\n{content}"
        
        # Split into smaller chunks based on rate limits
        # Assuming gpt-4o (30k TPM) - use 25k tokens = ~100k characters for safety
        chunks = chunk_text(full_content, chunk_size=100000)  # ~100k characters per chunk
        
        print(f"Story '{story_title}' split into {len(chunks)} chunks")
        all_chunks.extend(chunks)

print(f"\nTotal chunks to process: {len(all_chunks)}")

# Process chunks one at a time with delays
delay_between_chunks = 3  # Wait 3 seconds between chunks (rate limit is per minute)

for i, chunk in enumerate(all_chunks):
    print(f"\nProcessing chunk {i+1}/{len(all_chunks)} (length: {len(chunk)} chars)")
    
    try:
        rag.insert([chunk])  # Insert as single-item list
        print(f"✅ Successfully processed chunk {i+1}")
    except Exception as e:
        print(f"❌ Error processing chunk {i+1}: {e}")
        if "rate limit" in str(e).lower():
            print("⏳ Rate limit hit, waiting 15 seconds before retry...")
            time.sleep(15)
            try:
                rag.insert([chunk])
                print(f"✅ Successfully processed chunk {i+1} on retry")
            except Exception as retry_e:
                print(f"❌ Failed on retry: {retry_e}")
                break  # Stop if we keep hitting rate limits
    
    # Wait between chunks to respect rate limits
    if i + 1 < len(all_chunks):
        print(f"⏳ Waiting {delay_between_chunks} seconds before next chunk...")
        time.sleep(delay_between_chunks)

print("\n🎉 All chunks processed!")