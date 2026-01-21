import os
import sys
from typing import List, Tuple
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.config import CHROMA_PERSIST_DIR, CHUNK_SIZE, CHUNK_OVERLAP


class RAGPipeline:
    """Enhanced RAG Pipeline with PDF validation and content verification"""
    
    def __init__(self):
        """Initialize RAG pipeline with embeddings and vector store"""
        try:
            with st.spinner("Loading embedding model..."):
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'}
                )
            
            self.vector_store = None
            
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
            self._load_vector_store()
            
        except Exception as e:
            st.error(f"Failed to initialize RAG pipeline: {str(e)}")
            raise
    
    def _load_vector_store(self):
        """Load existing vector store if available"""
        try:
            if os.path.exists(CHROMA_PERSIST_DIR):
                if os.listdir(CHROMA_PERSIST_DIR):
                    self.vector_store = Chroma(
                        persist_directory=CHROMA_PERSIST_DIR,
                        embedding_function=self.embeddings
                    )
                    print("✅ Loaded existing vector store")
        except Exception as e:
            print(f"⚠️ Could not load existing vector store: {e}")
            self.vector_store = None
    
    def _validate_pdf_content(self, text: str, filename: str) -> Tuple[bool, str]:
        """Validate PDF content quality and relevance"""
        if len(text.strip()) < 100:
            return False, f"❌ '{filename}' has very little text content (less than 100 characters). Please upload PDFs with substantial content."
        
        non_alpha_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if non_alpha_ratio > 0.5:
            return False, f"⚠️ '{filename}' appears to have encoding issues or is mostly symbols. Please check the PDF quality."
        
        digit_ratio = sum(1 for c in text if c.isdigit()) / len(text)
        if digit_ratio > 0.7:
            return False, f"⚠️ '{filename}' appears to be mostly numerical data. For best results, upload PDFs with descriptive text content."
        
        suggestion = self._get_content_suggestions(text)
        
        return True, suggestion
    
    def _get_content_suggestions(self, text: str) -> str:
        """Analyze content and provide suggestions"""
        text_lower = text.lower()
        
        has_services = any(word in text_lower for word in ['service', 'appointment', 'booking', 'consultation'])
        has_pricing = any(word in text_lower for word in ['price', 'cost', 'dollar', 'fee', 'charge'])
        has_hours = any(word in text_lower for word in ['hours', 'open', 'available', 'schedule'])
        has_contact = any(word in text_lower for word in ['phone', 'email', 'contact', 'address'])
        
        suggestions = []
        
        if not has_services:
            suggestions.append("Consider including: Service descriptions and types")
        if not has_pricing:
            suggestions.append("Consider including: Pricing information")
        if not has_hours:
            suggestions.append("Consider including: Business hours and availability")
        if not has_contact:
            suggestions.append("Consider including: Contact information")
        
        if suggestions:
            return "💡 To improve Q&A quality, " + ", ".join(suggestions)
        else:
            return "✅ PDF content looks good with service information!"
    
    def extract_text_from_pdf(self, pdf_file) -> Tuple[bool, str]:
        """Extract text from uploaded PDF file with validation"""
        try:
            pdf_reader = PdfReader(pdf_file)
            
            if len(pdf_reader.pages) == 0:
                return False, "PDF file is empty (no pages found)"
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    print(f"⚠️ Error extracting text from page {page_num + 1}: {e}")
                    continue
            
            if not text.strip():
                return False, (
                    "No text could be extracted from PDF. "
                    "This might be a scanned document or image-based PDF. "
                    "Please upload PDFs with selectable text."
                )
            
            is_valid, message = self._validate_pdf_content(text, pdf_file.name)
            
            if not is_valid:
                return False, message
            
            return True, text
            
        except Exception as e:
            return False, f"Error reading PDF: {str(e)}"
    
    def detect_pdf_type(self, text: str) -> dict:
        """Detect what type of PDF was uploaded"""
        text_lower = text.lower()
        
        pdf_type = {
            'is_service_info': False,
            'is_ticket': False,
            'is_research': False,
            'is_invoice': False,
            'confidence': 'low',
            'message': ''
        }
        
        # Check for ticket/boarding pass
        ticket_keywords = ['boarding pass', 'ticket', 'flight', 'seat', 'gate', 'terminal', 'departure', 'arrival']
        if sum(1 for kw in ticket_keywords if kw in text_lower) >= 3:
            pdf_type['is_ticket'] = True
            pdf_type['confidence'] = 'high'
            pdf_type['message'] = "⚠️ This appears to be a ticket/boarding pass, not service information"
            return pdf_type
        
        # Check for research paper
        research_keywords = ['abstract', 'methodology', 'conclusion', 'references', 'fig.', 'table', 'experiment', 'dataset']
        if sum(1 for kw in research_keywords if kw in text_lower) >= 4:
            pdf_type['is_research'] = True
            pdf_type['confidence'] = 'high'
            pdf_type['message'] = "⚠️ This appears to be a research paper/academic document, not service information"
            return pdf_type
        
        # Check for invoice
        invoice_keywords = ['invoice', 'bill', 'amount due', 'total', 'payment', 'due date', 'invoice number']
        if sum(1 for kw in invoice_keywords if kw in text_lower) >= 3:
            pdf_type['is_invoice'] = True
            pdf_type['confidence'] = 'high'
            pdf_type['message'] = "⚠️ This appears to be an invoice/bill, not service information"
            return pdf_type
        
        # Check for service information
        service_keywords = ['service', 'appointment', 'booking', 'hours', 'contact', 'offer', 'price', 'menu']
        if sum(1 for kw in service_keywords if kw in text_lower) >= 3:
            pdf_type['is_service_info'] = True
            pdf_type['confidence'] = 'high'
            pdf_type['message'] = "✅ This looks like service information - perfect for Q&A!"
            return pdf_type
        
        pdf_type['confidence'] = 'low'
        pdf_type['message'] = "📄 PDF uploaded, but content type unclear"
        return pdf_type
    
    def get_suggested_questions(self, pdf_content: str) -> list:
        """Generate suggested questions based on PDF content"""
        content_lower = pdf_content.lower()
        
        suggestions = []
        
        if any(word in content_lower for word in ['service', 'offering', 'provide']):
            suggestions.append("What services do you offer?")
            suggestions.append("Tell me about your main services")
        
        if any(word in content_lower for word in ['price', 'cost', 'dollar', 'fee', 'charge', 'pricing']):
            suggestions.append("What are your prices?")
            suggestions.append("How much does [service] cost?")
        
        if any(word in content_lower for word in ['hours', 'open', 'available', 'schedule', 'timing']):
            suggestions.append("What are your business hours?")
            suggestions.append("When are you open?")
        
        if any(word in content_lower for word in ['phone', 'email', 'contact', 'address', 'location']):
            suggestions.append("How can I contact you?")
            suggestions.append("Where are you located?")
        
        if any(word in content_lower for word in ['appointment', 'booking', 'reservation']):
            suggestions.append("How do I make an appointment?")
            suggestions.append("What's your booking process?")
        
        if any(word in content_lower for word in ['policy', 'cancel', 'reschedule', 'refund']):
            suggestions.append("What's your cancellation policy?")
            suggestions.append("Can I reschedule my appointment?")
        
        suggestions.append("What should I know before booking?")
        suggestions.append("Do you have any special offers?")
        
        return suggestions[:6]
    
    def process_pdfs(self, pdf_files: List) -> Tuple[bool, str]:
        """Process PDFs with type detection and question suggestions"""
        if not pdf_files:
            return False, "No PDF files provided"
        
        try:
            all_documents = []
            processed_files = []
            failed_files = []
            warnings = []
            all_suggestions = []
            
            for pdf_file in pdf_files:
                success, result = self.extract_text_from_pdf(pdf_file)
                
                if not success:
                    failed_files.append(f"❌ {pdf_file.name}: {result}")
                    continue
                
                text = result
                
                pdf_type_info = self.detect_pdf_type(text)
                
                if pdf_type_info['is_ticket'] or pdf_type_info['is_research'] or pdf_type_info['is_invoice']:
                    warnings.append(f"⚠️ {pdf_file.name}: {pdf_type_info['message']}")
                
                _, suggestion = self._validate_pdf_content(text, pdf_file.name)
                if "Consider including" in suggestion:
                    warnings.append(f"📝 {pdf_file.name}: {suggestion}")
                
                if pdf_type_info['is_service_info']:
                    questions = self.get_suggested_questions(text)
                    all_suggestions.extend(questions)
                
                chunks = self.text_splitter.split_text(text)
                
                if not chunks:
                    failed_files.append(f"❌ {pdf_file.name}: No text chunks created")
                    continue
                
                documents = [
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": pdf_file.name,
                            "chunk_id": idx,
                            "total_chunks": len(chunks)
                        }
                    )
                    for idx, chunk in enumerate(chunks)
                ]
                
                all_documents.extend(documents)
                processed_files.append(pdf_file.name)
            
            if not all_documents:
                error_msg = "❌ Failed to process any PDFs.\n\n"
                if failed_files:
                    error_msg += "**Issues found:**\n" + "\n".join(failed_files)
                error_msg += "\n\n**📄 Upload service PDFs with:**\n"
                error_msg += "✓ Service descriptions\n✓ Pricing\n✓ Hours\n✓ Contact info\n\n"
                error_msg += "**Avoid:**\n✗ Tickets/boarding passes\n✗ Research papers\n✗ Invoices/bills\n✗ Scanned images"
                return False, error_msg
            
            if self.vector_store is None:
                self.vector_store = Chroma.from_documents(
                    documents=all_documents,
                    embedding=self.embeddings,
                    persist_directory=CHROMA_PERSIST_DIR
                )
            else:
                self.vector_store.add_documents(all_documents)
            
            self.vector_store.persist()
            
            if all_suggestions:
                st.session_state.pdf_suggestions = list(set(all_suggestions))[:6]
            
            success_msg = f"✅ **Successfully processed {len(processed_files)}/{len(pdf_files)} PDF(s)**\n\n"
            success_msg += f"📊 **Chunks created:** {len(all_documents)}\n\n"
            
            success_msg += "**Processed:**\n"
            for filename in processed_files:
                success_msg += f"✓ {filename}\n"
            
            if warnings:
                success_msg += "\n**⚠️ Notices:**\n"
                for warning in warnings:
                    success_msg += f"{warning}\n"
            
            if failed_files:
                success_msg += "\n**❌ Failed:**\n"
                for failure in failed_files:
                    success_msg += f"{failure}\n"
            
            if all_suggestions:
                success_msg += "\n\n💡 **Try asking:**\n"
                for q in list(set(all_suggestions))[:6]:
                    success_msg += f"• {q}\n"
            
            success_msg += "\n🎉 **Ready for questions!**"
            
            return True, success_msg
        
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    def query(self, question: str, k: int = 4) -> str:
        """Query the vector store and return relevant information"""
        try:
            if self.vector_store is None:
                return ""
            
            docs = self.vector_store.similarity_search(question, k=k)
            
            if not docs:
                return ""
            
            context_parts = []
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown')
                content = doc.page_content.strip()
                context_parts.append(f"[Source: {source}]\n{content}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            return context
        
        except Exception as e:
            print(f"Error querying documents: {str(e)}")
            return ""
    
    def get_relevant_docs(self, question: str, k: int = 4):
        """Get relevant documents with metadata"""
        try:
            if self.vector_store is None:
                return []
            
            docs = self.vector_store.similarity_search(question, k=k)
            return docs
        
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []
    
    def clear_vector_store(self) -> Tuple[bool, str]:
        """Clear the vector store and delete all stored documents"""
        try:
            if os.path.exists(CHROMA_PERSIST_DIR):
                import shutil
                shutil.rmtree(CHROMA_PERSIST_DIR)
                os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
            
            self.vector_store = None
            
            # Clear suggestions
            if hasattr(st.session_state, 'pdf_suggestions'):
                delattr(st.session_state, 'pdf_suggestions')
            
            return True, "✅ All documents cleared successfully"
        
        except Exception as e:
            return False, f"❌ Error clearing documents: {str(e)}"
    
    def get_stats(self) -> dict:
        """Get statistics about the vector store"""
        try:
            if self.vector_store is None:
                return {
                    "total_chunks": 0,
                    "sources": [],
                    "is_ready": False
                }
            
            collection = self.vector_store._collection
            all_docs = collection.get()
            
            sources = set()
            if all_docs and 'metadatas' in all_docs:
                for metadata in all_docs['metadatas']:
                    if metadata and 'source' in metadata:
                        sources.add(metadata['source'])
            
            return {
                "total_chunks": len(all_docs['ids']) if all_docs and 'ids' in all_docs else 0,
                "sources": list(sources),
                "is_ready": True
            }
        
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return {
                "total_chunks": 0,
                "sources": [],
                "is_ready": False
            }