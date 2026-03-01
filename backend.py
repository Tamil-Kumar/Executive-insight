import os
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

class LegalEngine:
    def __init__(self):
        # Note: Ensure OPENAI_API_KEY is set in your environment
        self.llm = OpenAI(model='gpt-3.5-turbo-instruct', temperature=0)
        
        self.csv_files = [
            'trump_eos.csv', 'biden.csv', 'carter.csv', 'clinton.csv', 'eisenhower.csv', 
            'ford.csv', 'h_w_bush.csv', 'johnson.csv', 'kennedy.csv', 'nixon.csv', 
            'obama.csv', 'past.csv', 'reagan.csv', 'roosevelt.csv', 'truman.csv', 
            'trump2.csv', 'w_bush.csv'
        ]
        
        self.all_data_content = [] 
        self._load_databases()

        # AI context slice (first 20 rows to stay within token limits)
        if self.all_data_content:
            self.csv_context = "\n\n".join(self.all_data_content[:20])
        else:
            self.csv_context = "No specific database records found."

        # AI Prompt Logic (Modern LCEL Chain)
        self.ai_template = """
        You are "Executive Insight", a professional legal research AI.
        Use the following database information to assist with the inquiry.
        If the information isn't in the database, use your general legal knowledge but stay formal.
        
        Database Context:
        {context}
        
        Question: {question}
        
        Disclaimer: This is for educational purposes and is not legal advice.
        Answer:"""
        
        self.prompt_obj = PromptTemplate.from_template(self.ai_template)
        
        # Modern Chain Construction
        self.chain = self.prompt_obj | self.llm | StrOutputParser()

    def _load_databases(self):
        """Loads all CSV files listed in csv_files into memory."""
        for file in self.csv_files:
            if os.path.exists(file):
                try:
                    loader = CSVLoader(file_path=file)
                    data = loader.load()
                    for doc in data:
                        self.all_data_content.append(doc.page_content)
                except Exception as e:
                    print(f"Error loading {file}: {e}")
            else:
                print(f"File not found: {file}")

    def query_ai(self, user_query):
        """Invokes the LangChain AI model."""
        return self.chain.invoke({"context": self.csv_context, "question": user_query})

    def search_records(self, query, limit=100):
        """Filters the loaded data content based on a keyword."""
        query = query.lower()
        matches = []
        count = 0
        for record in self.all_data_content:
            if query in record.lower():
                matches.append(record)
                count += 1
            if count >= limit:
                break
        return matches
