#!/bin/bash

# Script to download various datasets for LLM training

set -e

echo "🚀 Dataset Downloader for Demo LLM"
echo "=================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create data directory
DATA_DIR="data/datasets"
mkdir -p $DATA_DIR

print_menu() {
    echo ""
    echo "Available Datasets:"
    echo "1. TinyShakespeare (1MB) - Quick demo dataset"
    echo "2. WikiText-2 (12MB) - Small Wikipedia dataset" 
    echo "3. Simple Wikipedia (100MB) - Simplified English Wikipedia"
    echo "4. Custom Tech Docs - Generate technology documentation"
    echo "5. All of the above"
    echo ""
}

download_tiny_shakespeare() {
    echo -e "${BLUE}Downloading TinyShakespeare dataset...${NC}"
    curl -L https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt \
         -o $DATA_DIR/tinyshakespeare.txt
    echo -e "${GREEN}✅ TinyShakespeare downloaded${NC}"
}

download_wikitext() {
    echo -e "${BLUE}Downloading WikiText-2 dataset...${NC}"
    if [ ! -f $DATA_DIR/wikitext-2.zip ]; then
        curl -L https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip \
             -o $DATA_DIR/wikitext-2.zip
        unzip -q $DATA_DIR/wikitext-2.zip -d $DATA_DIR/
        rm $DATA_DIR/wikitext-2.zip
    fi
    echo -e "${GREEN}✅ WikiText-2 downloaded${NC}"
}

download_simple_wikipedia() {
    echo -e "${BLUE}Downloading Simple Wikipedia dataset...${NC}"
    echo -e "${YELLOW}Note: This is a larger download (100MB+)${NC}"
    
    # Using a subset for demo purposes
    curl -L https://huggingface.co/datasets/wikipedia/resolve/main/data/20220301.simple/train-00000-of-00001.parquet \
         -o $DATA_DIR/simple_wikipedia.parquet 2>/dev/null || {
        echo "Simple Wikipedia download failed, creating sample instead..."
        create_wikipedia_sample
    }
    echo -e "${GREEN}✅ Simple Wikipedia downloaded${NC}"
}

create_wikipedia_sample() {
    # Create a sample if download fails
    cat > $DATA_DIR/simple_wikipedia_sample.txt << 'EOF'
Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans.
Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience.
Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning.
Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language.
Computer vision is an interdisciplinary scientific field that deals with how computers can gain high-level understanding from digital images or videos.
EOF
}

generate_tech_docs() {
    echo -e "${BLUE}Generating technical documentation dataset...${NC}"
    
    python3 - << 'EOF'
import json
import random

tech_topics = [
    "Docker", "Kubernetes", "Python", "Machine Learning", "AWS", 
    "Git", "Linux", "REST APIs", "Databases", "Security"
]

templates = [
    "{topic} is a technology that helps developers {action}.",
    "To use {topic}, you need to understand {concept}.",
    "The main benefit of {topic} is {benefit}.",
    "{topic} works by {mechanism}.",
    "When working with {topic}, remember to {tip}.",
]

actions = ["build scalable applications", "automate workflows", "manage infrastructure", "process data efficiently"]
concepts = ["core principles", "basic commands", "architecture patterns", "best practices"]
benefits = ["improved performance", "better scalability", "easier maintenance", "reduced complexity"]
mechanisms = ["abstracting complexity", "providing APIs", "managing resources", "automating tasks"]
tips = ["follow documentation", "use version control", "test thoroughly", "monitor performance"]

docs = []
for _ in range(500):
    topic = random.choice(tech_topics)
    template = random.choice(templates)
    text = template.format(
        topic=topic,
        action=random.choice(actions),
        concept=random.choice(concepts),
        benefit=random.choice(benefits),
        mechanism=random.choice(mechanisms),
        tip=random.choice(tips)
    )
    docs.append(text)

with open('data/datasets/tech_docs.json', 'w') as f:
    json.dump({"texts": docs}, f, indent=2)

print(f"Generated {len(docs)} technical documentation examples")
EOF
    
    echo -e "${GREEN}✅ Tech docs generated${NC}"
}

prepare_for_training() {
    echo ""
    echo -e "${BLUE}Preparing datasets for training...${NC}"
    
    # Combine all text files into training format
    python3 - << 'EOF'
import os
import json
import glob

data_dir = "data/datasets"
all_texts = []

# Read all text files
for txt_file in glob.glob(f"{data_dir}/*.txt"):
    print(f"Processing {txt_file}...")
    with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        # Split into sentences or paragraphs
        texts = [t.strip() for t in content.split('\n') if t.strip() and len(t.strip()) > 20]
        all_texts.extend(texts[:1000])  # Limit each file to 1000 lines for demo

# Read JSON files
for json_file in glob.glob(f"{data_dir}/*.json"):
    print(f"Processing {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
        if 'texts' in data:
            all_texts.extend(data['texts'])

# Create final training file
output = {
    "texts": all_texts,
    "metadata": {
        "total_examples": len(all_texts),
        "sources": os.listdir(data_dir)
    }
}

with open('data/training_data.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Combined {len(all_texts)} text examples into data/training_data.json")
EOF
}

# Main menu
print_menu

echo -n "Select dataset to download (1-5): "
read choice

case $choice in
    1)
        download_tiny_shakespeare
        ;;
    2)
        download_wikitext
        ;;
    3)
        download_simple_wikipedia
        ;;
    4)
        generate_tech_docs
        ;;
    5)
        download_tiny_shakespeare
        download_wikitext
        generate_tech_docs
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Prepare for training
prepare_for_training

echo ""
echo -e "${GREEN}✅ Dataset preparation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review the data in data/training_data.json"
echo "2. Run training: ./scripts/docker-pipeline.sh train"
echo "3. Monitor progress in MLflow: http://localhost:5001"