import os
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

# Step 1: Set up OpenAI API Key
os.environ["OPENAI_API_KEY"] = "sk-..."

# Step 2: Set up Neo4j credentials
os.environ["NEO4J_URI"] = "bolt://localhost:7687"  # Adjust if necessary
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"

# Step 3: Initialize Neo4j connection
graph = Neo4jGraph()

# Step 4: Delete the existing graph in Neo4j (deletes all nodes and relationships)
def delete_existing_graph():
    delete_query = """
    MATCH (n)
    DETACH DELETE n
    """
    with graph._driver.session() as session:
        session.run(delete_query)
    print("Existing graph deleted.")

delete_existing_graph()

# Step 5: Initialize the LLM model (OpenAI GPT-4 Turbo)
llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

# Step 6: Initialize the LLM Graph Transformer
llm_transformer = LLMGraphTransformer(llm=llm)

# Step 7: Read the text from the uploaded .txt file
file_path = "english.txt"  # Path to the uploaded file
with open(file_path, "r", encoding="utf-8") as file:
    text = file.read()

# Step 8: Convert the text into a Document format for LangChain processing
documents = [Document(page_content=text)]

# Step 9: Use the LLM to extract graph information (nodes and relationships)
graph_documents = llm_transformer.convert_to_graph_documents(documents)

# Step 10: Display the extracted nodes and relationships (for debugging/inspection)
print(f"Nodes: {graph_documents[0].nodes}")
print(f"Relationships: {graph_documents[0].relationships}")

# Optional: Filter specific node and relationship types
llm_transformer_filtered = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=["Food", "Category"],
    allowed_relationships=["CAN_BE_EATEN", "SHOULD_BE_AVOIDED"]
)
graph_documents_filtered = llm_transformer_filtered.convert_to_graph_documents(documents)

print(f"Filtered Nodes: {graph_documents_filtered[0].nodes}")
print(f"Filtered Relationships: {graph_documents_filtered[0].relationships}")

# Step 11: Store the extracted graph into Neo4j
#graph.add_graph_documents(graph_documents_filtered)
graph.add_graph_documents(graph_documents)


# Confirm graph storage
print("Graph has been successfully stored in Neo4j!")
