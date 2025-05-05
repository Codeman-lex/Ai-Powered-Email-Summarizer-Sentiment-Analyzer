import os
from typing import Dict, List, Any, Optional, Tuple
import structlog
from openai import OpenAI
from langchain.llms import OpenAI as LangchainOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import spacy
from transformers import pipeline
import numpy as np
from app.utils.caching import cache

logger = structlog.get_logger(__name__)

class AiService:
    """Service for AI-powered email analysis"""
    
    def __init__(self):
        """Initialize AI service and load models"""
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Load NLP models
        try:
            self.nlp = spacy.load("en_core_web_md")
        except Exception:
            logger.warning("Could not load SpaCy model, downloading now...")
            import spacy.cli
            spacy.cli.download("en_core_web_md")
            self.nlp = spacy.load("en_core_web_md")
        
        # Initialize sentiment model
        self.sentiment_model = pipeline(
            "sentiment-analysis", 
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=0 if os.getenv("USE_GPU", "false").lower() == "true" else -1
        )
        
        # Initialize LangChain components
        self.llm = LangchainOpenAI(temperature=0, model_name="gpt-3.5-turbo-instruct")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        logger.info("AI service initialized successfully")
    
    @cache(ttl=3600)
    def analyze_email_content(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on email content
        
        Args:
            email: Email data dictionary
            
        Returns:
            Dictionary containing various analyses
        """
        text = email.get("body", "")
        subject = email.get("subject", "")
        
        if not text:
            return {
                "summary": "No content to analyze",
                "sentiment": "neutral",
                "entities": [],
                "categories": [],
                "importance_score": 0.0,
                "action_items": [],
                "topics": []
            }
        
        # Run analyses in parallel/concurrently in a production system
        summary = self._generate_summary(subject, text)
        sentiment, sentiment_score = self._analyze_sentiment(text)
        entities = self._extract_entities(text)
        categories = self._categorize_email(subject, text)
        importance_score = self._calculate_importance(subject, text, entities)
        action_items = self._extract_action_items(text)
        topics = self._extract_topics(text)
        
        return {
            "summary": summary,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "entities": entities,
            "categories": categories,
            "importance_score": importance_score,
            "action_items": action_items,
            "topics": topics
        }
    
    def enhance_search_query(self, query: str) -> str:
        """
        Enhance a search query with AI to improve relevance
        
        Args:
            query: Original search query
            
        Returns:
            Enhanced search query
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that helps improve search queries for email search. Expand this query with relevant keywords and synonyms to improve search results, but keep it concise."},
                    {"role": "user", "content": f"Original query: {query}"}
                ],
                max_tokens=100,
                temperature=0.3
            )
            enhanced_query = response.choices[0].message.content.strip()
            logger.info("Enhanced search query", original=query, enhanced=enhanced_query)
            return enhanced_query
        except Exception as e:
            logger.error("Error enhancing search query", error=str(e))
            return query  # Fallback to original query if enhancement fails
    
    def _generate_summary(self, subject: str, text: str) -> str:
        """Generate a concise summary of email content"""
        try:
            # For shorter emails, use direct OpenAI call
            if len(text) < 4000:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an email summarization assistant. Provide a concise summary of the email in 1-2 sentences."},
                        {"role": "user", "content": f"Subject: {subject}\n\nEmail: {text}"}
                    ],
                    max_tokens=100,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            
            # For longer emails, use LangChain's summarize chain
            docs = [Document(page_content=chunk) for chunk in self.text_splitter.split_text(text)]
            chain = load_summarize_chain(self.llm, chain_type="map_reduce")
            summary = chain.run(docs)
            return summary.strip()
        
        except Exception as e:
            logger.error("Error generating summary", error=str(e))
            return "Could not generate summary."
    
    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment of email content"""
        try:
            # Use shorter text for transformer model
            truncated_text = text[:512] if len(text) > 512 else text
            result = self.sentiment_model(truncated_text)[0]
            
            label = result["label"].lower()
            score = result["score"]
            
            # Map to standardized sentiment labels
            if label == "positive" or (label == "neutral" and score > 0.7):
                return "positive", score
            elif label == "negative" or (label == "neutral" and score < 0.3):
                return "negative", score
            else:
                return "neutral", score
                
        except Exception as e:
            logger.error("Error analyzing sentiment", error=str(e))
            return "neutral", 0.5
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from email content"""
        try:
            doc = self.nlp(text[:10000])  # Limit text length for performance
            
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
            
            return entities
        except Exception as e:
            logger.error("Error extracting entities", error=str(e))
            return []
    
    def _categorize_email(self, subject: str, text: str) -> List[str]:
        """Categorize email into business-relevant categories"""
        try:
            prompt = f"""
            Please categorize the following email into one or more of these categories:
            - Urgent
            - Action Required
            - Meeting
            - Information
            - Project Update
            - External Client
            - Internal Team
            - Personal
            - Marketing
            - Sales
            - HR
            - Finance
            - Technical
            
            Return only the category names as a comma-separated list.
            
            Subject: {subject}
            
            Email: {text[:1000]}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an email categorization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            categories = [
                cat.strip() 
                for cat in response.choices[0].message.content.split(",")
                if cat.strip()
            ]
            
            return categories
            
        except Exception as e:
            logger.error("Error categorizing email", error=str(e))
            return ["Uncategorized"]
    
    def _calculate_importance(self, subject: str, text: str, entities: List[Dict[str, Any]]) -> float:
        """Calculate importance score of email based on content and metadata"""
        try:
            # Simple heuristic importance calculation, would be more sophisticated in production
            importance = 0.0
            
            # Check for urgent keywords
            urgent_keywords = ["urgent", "asap", "immediately", "deadline", "important", "critical"]
            if any(word in subject.lower() for word in urgent_keywords):
                importance += 0.4
            if any(word in text.lower()[:500] for word in urgent_keywords):
                importance += 0.2
                
            # Check for action verbs
            action_keywords = ["please", "request", "action", "review", "approve", "confirm"]
            if any(word in text.lower()[:1000] for word in action_keywords):
                importance += 0.2
                
            # Check for named entities of interest
            person_entities = [e for e in entities if e["label"] in ["PERSON", "ORG"]]
            importance += min(len(person_entities) * 0.05, 0.2)
            
            # Normalize to 0-1 range
            return min(max(importance, 0.0), 1.0)
            
        except Exception as e:
            logger.error("Error calculating importance", error=str(e))
            return 0.5
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items and tasks from email content"""
        try:
            prompt = f"""
            Extract any action items, tasks, or requests from this email.
            Return them as a list of concise bullet points.
            If there are no action items, return an empty list.
            
            Email: {text[:2000]}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an assistant that extracts action items from emails."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Process the response to extract clean action items
            action_items = []
            for line in content.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*") or any(c.isdigit() for c in line[:2])):
                    # Clean up line from bullet points or numbers
                    item = line.lstrip("-*0123456789. ")
                    if item:
                        action_items.append(item)
            
            return action_items
            
        except Exception as e:
            logger.error("Error extracting action items", error=str(e))
            return []
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from email content"""
        try:
            prompt = f"""
            Extract the main topics or themes from this email.
            Return them as a list of 2-4 keywords or short phrases.
            
            Email: {text[:1500]}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an assistant that extracts main topics from text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Process the response to extract clean topics
            topics = []
            for line in content.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*") or any(c.isdigit() for c in line[:2])):
                    # Clean up line from bullet points or numbers
                    topic = line.lstrip("-*0123456789. ")
                    if topic:
                        topics.append(topic)
            
            return topics
            
        except Exception as e:
            logger.error("Error extracting topics", error=str(e))
            return [] 