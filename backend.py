import os
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.output_parsers import StrOutputParser

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
        self.csv_context = "\n\n".join(self.all_data_content[:20]) if self.all_data_content else "No records found."

        # Modern LCEL Chain
        template = """
        You are "Executive Insight", a professional legal research AI.
        Use the following database information to assist with the inquiry.
        
        Database Context:
        {context}
        
        Question: {question}
        
        Disclaimer: This is for educational purposes and is not legal advice.
        Answer:"""
        
        prompt = PromptTemplate.from_template(template)
        self.chain = prompt | self.llm | StrOutputParser()

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
        """Invoke the AI chain with the current context."""
        return self.chain.invoke({"context": self.csv_context, "question": user_query})

    def search_records(self, query, limit=100):
        """Filters the raw CSV data for the search tab."""
        matches = []
        query = query.lower()
        for record in self.all_data_content:
            if query in record.lower():
                matches.append(record)
            if len(matches) >= limit:
                break
        return matches
