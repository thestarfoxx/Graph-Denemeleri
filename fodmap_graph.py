import re
from neo4j import GraphDatabase

# Neo4j connection details
uri = "bolt://localhost:7687"  # Default Neo4j bolt URI
username = "neo4j"
password = "password"  # Set your Neo4j password

# Connect to Neo4j database
driver = GraphDatabase.driver(uri, auth=(username, password))

# Function to parse the text file
def parse_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Using regex to split into sections (Foods to Avoid, Foods You Can Eat)
    avoid_section = re.search(r"Foods to Avoid:\n(.*?)\n\n", content, re.DOTALL)
    eat_section = re.search(r"Foods You Can Eat:\n(.*?)$", content, re.DOTALL)
    
    if avoid_section:
        avoid_text = avoid_section.group(1).strip()
    else:
        avoid_text = ""

    if eat_section:
        eat_text = eat_section.group(1).strip()
    else:
        eat_text = ""

    # Extract categories and foods in each section
    avoid_categories = extract_foods_by_category(avoid_text)
    eat_categories = extract_foods_by_category(eat_text)
    
    return avoid_categories, eat_categories

# Function to extract foods and group them by category
def extract_foods_by_category(text):
    category_dict = {}
    lines = text.split("\n")
    current_category = None

    for line in lines:
        if line.strip() == "":
            continue
        if not line.startswith("    "):  # Category title
            current_category = line.strip(":")
            category_dict[current_category] = {}
        else:  # Food group and items
            if current_category:
                match = re.match(r"\s+(.*?):\s(.*)", line)
                if match:
                    group = match.group(1).strip()
                    foods = [food.strip() for food in match.group(2).split(",")]
                    category_dict[current_category][group] = foods
    return category_dict

# Function to create nodes and relationships in Neo4j
def create_knowledge_graph(tx, categories, relation_type):
    for category, groups in categories.items():
        tx.run("MERGE (:Category {name: $category})", category=category)
        for group, foods in groups.items():
            tx.run("MERGE (:Group {name: $group})", group=group)
            tx.run("""
                MATCH (c:Category {name: $category}), (g:Group {name: $group})
                MERGE (g)-[:HAS_CATEGORY]->(c)
            """, category=category, group=group)
            for food in foods:
                tx.run("MERGE (:Food {name: $food})", food=food)
                tx.run("""
                    MATCH (f:Food {name: $food}), (g:Group {name: $group})
                    MERGE (f)-[:BELONGS_TO]->(g)
                """, food=food, group=group)
                # Instead of creating a Recommendation node, use the relationship directly
                tx.run(f"""
                    MATCH (f:Food {{name: $food}}), (g:Group {{name: $group}})
                    MERGE (f)-[:{relation_type}]->(g)
                """, food=food, group=group)

# Main function to extract, process and create the knowledge graph
def main(file_path):
    # Parse the text file
    avoid_categories, eat_categories = parse_text(file_path)
    
    # Create knowledge graph in Neo4j
    with driver.session() as session:
        # Create nodes and relationships for foods to avoid
        session.write_transaction(create_knowledge_graph, avoid_categories, "SHOULD_BE_AVOIDED")

        # Create nodes and relationships for foods to eat
        session.write_transaction(create_knowledge_graph, eat_categories, "CAN_BE_EATEN")

    print("Knowledge graph created successfully!")

# Specify your file path
file_path = "english.txt"  # Path to your .txt file

# Run the main function
if __name__ == "__main__":
    main(file_path)
