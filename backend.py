import os
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.output_parsers import StrOutputParser

# This loads the variables from .env into the environment
load_dotenv()

class LegalEngine:
    def __init__(self):
        # LangChain's OpenAI object automatically looks for 
        # an environment variable named 'OPENAI_API_KEY'
        self.llm = OpenAI(model='gpt-3.5-turbo-instruct', temperature=0)
        
        self.csv_files = [
            'trump_eos.csv', 'biden.csv', 'carter.csv', 'clinton.csv', 'eisenhower.csv', 
            'ford.csv', 'h_w_bush.csv', 'johnson.csv', 'kennedy.csv', 'nixon.csv', 
            'obama.csv', 'past.csv', 'reagan.csv', 'roosevelt.csv', 'truman.csv', 
            'trump2.csv', 'w_bush.csv'
        ]
        
        self.all_data_content = [] 
        self._load_databases()

        # Context slice for AI (first 20 records)
        if self.all_data_content:
            self.csv_context = "\n\n".join(self.all_data_content[:20])
        else:
            self.csv_context = "No specific database records found."

        template = """
        You are "Executive Insight", a professional legal research AI.
        Context: {context}
        Question: {question}
        Answer:"""
        
        self.prompt_obj = PromptTemplate.from_template(template)
        self.chain = self.prompt_obj | self.llm | StrOutputParser()

    def _load_databases(self):
        for file in self.csv_files:
            if os.path.exists(file):
                try:
                    loader = CSVLoader(file_path=file)
                    data = loader.load()
                    for doc in data:
                        self.all_data_content.append(doc.page_content)
                except Exception as e:
                    print(f"Error loading {file}: {e}")

    def query_ai(self, user_query):
        return self.chain.invoke({"context": self.csv_context, "question": user_query})

    def search_records(self, query, limit=100):
        query = query.lower()
        return [r for r in self.all_data_content if query in r.lower()][:limit]
