"""Core chatbot logic for the hiring assistant."""

import openai
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re
from .prompt_manager import PromptManager
from .data_handler import DataHandler
from .question_generator import QuestionGenerator


class ConversationPhase(Enum):
    """Enumeration for different conversation phases."""

    GREETING = "greeting"
    INFO_GATHERING = "info_gathering"
    TECH_STACK = "tech_stack"
    TECHNICAL_QUESTIONS = "technical_questions"
    CLOSING = "closing"
    ENDED = "ended"


class HiringChatbot:
    """Main chatbot class for handling hiring conversations."""

    def __init__(self, api_key: str, model_name: str = "gpt-4.1"):
        """Initialize the chatbot with OpenAI API."""
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
        self.prompt_manager = PromptManager()
        self.data_handler = DataHandler()
        self.question_generator = QuestionGenerator()

        # Conversation state
        self.phase = ConversationPhase.GREETING
        self.candidate_data = {}
        self.current_questions = []
        self.current_question_index = 0
        self.conversation_history = []

        # Info gathering checklist
        self.required_info = [
            ("full_name", "What is your full name?"),
            ("email", "What is your email address?"),
            ("phone", "What is your phone number?"),
            (
                "experience_years",
                "How many years of professional experience do you have?",
            ),
            ("desired_positions", "What position(s) are you interested in?"),
            ("location", "What is your current location?"),
        ]
        self.current_info_index = 0

        # Add duplicate handling state
        self.pending_duplicate_check = False
        self.pending_field_name = None
        self.pending_field_value = None

    def _classify_user_input(
        self, user_message: str, expected_field: str = None
    ) -> Dict:
        """Classify user input to determine if it's appropriate for the expected field."""
        message_lower = user_message.lower().strip()

        # Question indicators
        question_words = [
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "which",
            "can you",
            "could you",
            "would you",
            "do you",
            "are you",
            "is it",
            "does it",
        ]
        is_question = any(
            word in message_lower for word in question_words
        ) or user_message.strip().endswith("?")

        # Check if it's a greeting or casual response
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon"]
        is_greeting = any(greeting in message_lower for greeting in greetings)

        return {
            "is_question": is_question,
            "is_greeting": is_greeting,
            "is_appropriate_for_field": self._is_appropriate_for_field(
                user_message, expected_field
            ),
            "message": user_message.strip(),
        }

    def _is_appropriate_for_field(self, message: str, field: str) -> bool:
        """Check if the message is appropriate for the expected field."""
        if not field:
            return True

        message_lower = message.lower().strip()

        # Question indicators
        question_words = [
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "which",
            "can you",
            "could you",
            "would you",
            "do you",
            "are you",
            "is it",
            "does it",
        ]
        is_question = any(
            word in message_lower for word in question_words
        ) or message.strip().endswith("?")

        if field == "full_name":
            # Name should not be a question and should be reasonable length
            return (
                not is_question
                and len(message.split()) <= 4
                and len(message.strip()) > 0
            )

        elif field == "email":
            # Should contain @ symbol
            return "@" in message and not is_question

        elif field == "phone":
            # Should contain digits
            return any(char.isdigit() for char in message) and not is_question

        elif field == "experience_years":
            # Should contain numbers or experience-related words
            has_number = any(char.isdigit() for char in message)
            exp_words = ["year", "month", "experience", "worked"]
            has_exp_words = any(word in message_lower for word in exp_words)
            return (has_number or has_exp_words) and not is_question

        return True

    def _handle_closing(self, user_message: str) -> str:
        self.phase = ConversationPhase.ENDED
        return "Thank you for taking the time to speak with us today. Have a great day!"

    def process_message(self, user_message: str, session_id: str) -> Tuple[str, bool]:
        """Process user message and return response with conversation status."""
    
        # Check for conversation ending keywords (now more restrictive)
        if self._is_ending_message(user_message):
            return self._handle_conversation_end(), True
    
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
    
        # Check if this is a natural conversation attempt
        is_natural_chat = self._is_natural_conversation(user_message)
    
        # Process based on current phase
        if self.phase == ConversationPhase.GREETING:
            response = self._handle_greeting(user_message)
        elif self.phase == ConversationPhase.INFO_GATHERING:
            if is_natural_chat and self.natural_conversation_count < self.max_natural_responses:
                response = self._handle_natural_conversation(user_message, "info_gathering")
            else:
                response = self._handle_info_gathering(user_message)
        elif self.phase == ConversationPhase.TECH_STACK:
            if is_natural_chat and self.natural_conversation_count < self.max_natural_responses:
                response = self._handle_natural_conversation(user_message, "tech_stack")
            else:
                response = self._handle_tech_stack(user_message)
        elif self.phase == ConversationPhase.TECHNICAL_QUESTIONS:
            if is_natural_chat and self.natural_conversation_count < self.max_natural_responses:
                response = self._handle_natural_conversation(user_message, "technical_questions")
            else:
                response = self._handle_technical_questions(user_message)
        elif self.phase == ConversationPhase.CLOSING:
            # In closing phase, allow more natural conversation
            if not self._is_definitive_goodbye(user_message):
                response = self._handle_closing_conversation(user_message)
            else:
                response = self._handle_closing(user_message)
        else:
            response = "I'm sorry, there seems to be an issue. Let me restart our conversation."
            self.phase = ConversationPhase.GREETING
    
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
    
        # Determine if conversation should end
        conversation_ended = self.phase == ConversationPhase.ENDED
    
        # Save data if in closing phase but not ended
        if self.phase == ConversationPhase.CLOSING and not conversation_ended:
            success, message = self.data_handler.save_candidate(self.candidate_data, session_id)
            if not success:
                print(f"Save failed: {message}")
    
        return response, conversation_ended
    



    def _is_natural_conversation(self, message: str) -> bool:
        """Check if message is natural conversation rather than direct answer."""
        message_lower = message.lower().strip()
    
        # Natural conversation indicators
        natural_indicators = [
            'how are you', 'nice to meet', 'thank you', 'thanks', 'cool', 'interesting',
            'wow', 'really', 'oh', 'i see', 'that sounds', 'how long have you',
            'what do you think', 'can you tell me', 'i was wondering'
        ]
    
        # Questions that aren't direct answers
        is_question = message.strip().endswith('?')
    
        return any(indicator in message_lower for indicator in natural_indicators) or (
            is_question and not self._looks_like_direct_answer(message)
        )

    def _looks_like_direct_answer(self, message: str) -> bool:
        """Check if message looks like a direct answer to our questions."""
        message_lower = message.lower()
    
        # If we're in info gathering phase, check for direct answers
        if self.phase == ConversationPhase.INFO_GATHERING:
            if self.current_info_index < len(self.required_info):
                field_name, _ = self.required_info[self.current_info_index]
                return self._is_appropriate_for_field(message, field_name)
    
        return False

    def _is_definitive_goodbye(self, message: str) -> bool:
        """Check if message is a definitive goodbye."""
        definitive_goodbyes = [
            'goodbye', 'bye bye', 'see you later', 'have a good day',
            'talk to you later', 'catch you later'
        ]
        return any(goodbye in message.lower() for goodbye in definitive_goodbyes)

    def _handle_closing_conversation(self, user_message: str) -> str:
        """Handle conversation in closing phase without ending immediately."""
        message_lower = user_message.lower()
    
        if any(word in message_lower for word in ['when', 'how long', 'timeline']):
            return """Typically, our team reviews applications within 2-3 business days. If there's a good match, we'll reach out for the next steps. 

Is there anything else you'd like to know about our process or the company?"""
    
        elif any(word in message_lower for word in ['what happens', 'next steps', 'process']):
            return """After this conversation, your information goes to our technical team for review. If selected, you'll hear from us for a more detailed technical interview.

Any other questions about what to expect?"""
    
        elif any(word in message_lower for word in ['company', 'about', 'culture']):
            return """TalentScout works with various tech companies to find the right fit for candidates. Each company has its own culture and requirements, which we'll discuss if there's a match.

Would you like to know anything else?"""
    
        else:
            return """I appreciate your interest! Our team will be in touch if there's a good match with our current opportunities.

Is there anything else you'd like to ask before we wrap up?"""
    








    def _is_ending_message(self, message: str) -> bool:
        """Check if message indicates user wants to end conversation."""
        ending_keywords = [
            "bye",
            "goodbye",
            "exit",
            "quit",
            "thanks",
            "thank you",
            "done",
            "finish",
        ]
        return any(keyword in message.lower() for keyword in ending_keywords)

    def _handle_greeting(self, user_message: str) -> str:
        """Handle greeting phase."""
        if not self.conversation_history or len(self.conversation_history) <= 1:
            # Initial greeting
            self.phase = ConversationPhase.INFO_GATHERING
            self._reset_natural_conversation_counter()
            return """Hello! Welcome to TalentScout's hiring assistant. I'm here to help with your initial screening process.

I'll be collecting some basic information about you and then asking a few technical questions based on your skills. This should take about 10-15 minutes.
 
Let's start with your basic information. What is your full name?"""
        else:
            # User responded to greeting
            self.phase = ConversationPhase.INFO_GATHERING
            return "Great! Let's begin with collecting your information. What is your full name?"

    def _handle_info_gathering(self, user_message: str) -> str:
        """Handle information gathering phase."""
        # Handle duplicate confirmation first
        if self.pending_duplicate_check:
            return self._handle_duplicate_confirmation(user_message)

        if self.current_info_index < len(self.required_info):
            field_name, question = self.required_info[self.current_info_index]

            # For the first question (name), we need to validate the response
            if self.current_info_index == 0 or field_name == "full_name":
                # Check if it's a question instead of a name
                classification = self._classify_user_input(user_message, field_name)

                if classification["is_question"]:
                    response = self._handle_user_question(user_message, field_name)
                    return response

                # Validate and store
                is_valid, error_msg = self._validate_and_store_field(
                    field_name, user_message
                )

                if not is_valid:
                    return f"{error_msg}"

                # Move to next field
                self.current_info_index += 1

                if self.current_info_index < len(self.required_info):
                    next_field, next_question = self.required_info[
                        self.current_info_index
                    ]
                    return f"Nice to meet you, {self.candidate_data['full_name']}! {next_question}"

            else:
                # Handle subsequent fields
                classification = self._classify_user_input(user_message, field_name)

                if classification["is_question"]:
                    return self._handle_user_question(user_message, field_name)

                is_valid, error_msg = self._validate_and_store_field(
                    field_name, user_message
                )

                if not is_valid:
                    return f"{error_msg}"

                # Move to next field
                self.current_info_index += 1

                if self.current_info_index < len(self.required_info):
                    next_field, next_question = self.required_info[
                        self.current_info_index
                    ]
                    return f"Thank you! {next_question}"
                else:
                    # All basic info collected, move to tech stack
                    self.phase = ConversationPhase.TECH_STACK
                    self._reset_natural_conversation_counter()
                    return f"""Perfect, {self.candidate_data['full_name']}! Now I'd like to learn about your technical skills.

Please tell me about your tech stack including:
- Programming languages you're proficient in
- Frameworks you've worked with  
- Databases you have experience with
- Tools and technologies you use

Just list them naturally, and I'll organize them for our discussion."""

        return "Let me get your information organized..."

    def _handle_duplicate_confirmation(self, user_message: str) -> str:
        """Handle the duplicate confirmation response."""
        user_response = user_message.lower().strip()

        # Check if user confirms they've applied before
        if user_response in ["yes", "y", "yeah", "yep", "true", "correct"]:
            # User has applied before - end conversation or handle appropriately
            self.phase = ConversationPhase.ENDED
            return """Thank you for confirming. Since you've already applied, our team has your information on file. 

If you'd like to update your information or apply for a different position, please contact our team directly.

Have a great day!"""

        elif user_response in ["no", "n", "nope", "false", "incorrect"]:
            # User hasn't applied before - continue with the pending field
            self.candidate_data[self.pending_field_name] = self.pending_field_value

            # Clear the pending state
            self.pending_duplicate_check = False
            field_name = self.pending_field_name
            self.pending_field_name = None
            self.pending_field_value = None

            # Move to next field
            self.current_info_index += 1

            if self.current_info_index < len(self.required_info):
                next_field, next_question = self.required_info[self.current_info_index]
                if field_name == "full_name":
                    return f"Nice to meet you, {self.candidate_data['full_name']}! {next_question}"
                else:
                    return f"Thank you! {next_question}"
            else:
                # All basic info collected, move to tech stack
                self.phase = ConversationPhase.TECH_STACK
                self._reset_natural_conversation_counter()
                return f"""Perfect, {self.candidate_data['full_name']}! Now I'd like to learn about your technical skills.

Please tell me about your tech stack including:
- Programming languages you're proficient in
- Frameworks you've worked with  
- Databases you have experience with
- Tools and technologies you use

Just list them naturally, and I'll organize them for our discussion."""

        else:
            # Unclear response - ask again
            
            return "Please answer with 'yes' or 'no' - have you applied with TalentScout before?"

    def _validate_and_store_field(
        self, field_name: str, value: str
    ) -> Tuple[bool, str]:
        """Validate and store a field value."""
        # First classify the input
        classification = self._classify_user_input(value, field_name)

        # Handle questions or inappropriate responses
        if classification["is_question"]:
            if field_name == "full_name":
                return (
                    False,
                    "I understand you have a question, but I need your full name first. Could you please tell me your name?",
                )
            elif field_name == "email":
                return (
                    False,
                    "I'd be happy to answer questions, but I need your email address first. What's your email?",
                )
            elif field_name == "phone":
                return (
                    False,
                    "I can help with questions later, but could you please provide your phone number first?",
                )
            elif field_name == "experience_years":
                return (
                    False,
                    "I'll answer questions in a moment, but first could you tell me how many years of experience you have?",
                )
            else:
                return (
                    False,
                    f"I'd like to answer your question, but could you first provide the information I asked for?",
                )

        if not classification["is_appropriate_for_field"]:
            if field_name == "full_name":
                return (
                    False,
                    "That doesn't look like a name. Could you please tell me your full name? For example: 'John Smith'",
                )
            elif field_name == "email":
                return (
                    False,
                    "That doesn't appear to be an email address. Please provide your email (e.g., john@example.com)",
                )
            elif field_name == "phone":
                return (
                    False,
                    "I need a valid phone number. Please provide your phone number with digits.",
                )

        # Clean the value
        cleaned_value = value.strip()

        # Rest of your existing validation logic...
        if field_name == "experience_years":
            numbers = re.findall(r"\d+", cleaned_value)
            if numbers:
                cleaned_value = int(numbers[0])
            else:
                return False, "Please provide your years of experience as a number."

        elif field_name == "desired_positions":
            positions = [
                pos.strip() for pos in re.split(r"[,\n]", cleaned_value) if pos.strip()
            ]
            cleaned_value = positions

        # Validate using data handler
        is_valid, error_msg = self.data_handler.validate_field(
            field_name, cleaned_value
        )

        if is_valid:
            if field_name in ["email", "full_name", "phone"]:
                temp_data = self.candidate_data.copy()
                temp_data[field_name] = cleaned_value

                is_duplicate, duplicate_msg = (
                    self.data_handler.check_duplicate_candidate(temp_data)
                )
                if is_duplicate:
                    # Set up pending duplicate check instead of immediate return
                    self.pending_duplicate_check = True
                    self.pending_field_name = field_name
                    self.pending_field_value = cleaned_value
                    return (
                        False,
                        f"{duplicate_msg}. Have you applied before? Please answer 'yes' or 'no'.",
                    )

            self.candidate_data[field_name] = cleaned_value
            return True, ""
        else:
            return False, error_msg

    def _handle_user_question(
        self, user_message: str, current_field: str = None
    ) -> str:
        """Handle user questions contextually while maintaining conversation flow."""
        message_lower = user_message.lower()

        # Common questions and responses
        if any(word in message_lower for word in ["how long", "time", "minutes"]):
            return f"This process typically takes 10-15 minutes. Now, could you please tell me your {current_field.replace('_', ' ')}?"

        elif any(word in message_lower for word in ["why", "purpose", "reason"]):
            return f"We're collecting this information for our initial screening to match you with suitable opportunities. Could you please provide your {current_field.replace('_', ' ')}?"

        elif any(word in message_lower for word in ["what happens", "next", "after"]):
            return f"After collecting your information, I'll ask some technical questions, then our team will review everything. For now, could you share your {current_field.replace('_', ' ')}?"

        elif any(word in message_lower for word in ["safe", "secure", "privacy"]):
            return f"Your information is securely stored and only used for recruitment purposes. Now, may I have your {current_field.replace('_', ' ')}?"

        else:
            return f"That's a good question! I'll be happy to discuss more details after we collect the basic information. Could you please tell me your {current_field.replace('_', ' ')} first?"
        


    def _handle_natural_conversation(self, user_message: str, current_phase: str) -> str:
    
        self.natural_conversation_count += 1
    
        message_lower = user_message.lower()
    
        # Handle common conversational responses
        if any(word in message_lower for word in ['how are you', 'how do you do', 'nice to meet']):
            response = "Thank you! I'm doing well and excited to learn more about you. "
        elif any(word in message_lower for word in ['thank you', 'thanks', 'appreciate']):
            response = "You're very welcome! "
        elif any(word in message_lower for word in ['interesting', 'cool', 'nice', 'great']):
            response = "I'm glad you think so! "
        elif '?' in user_message and not any(field in message_lower for field in ['name', 'email', 'phone', 'experience']):
            # Handle general questions
            response = "That's a great question! I'll be happy to discuss that further. "
        else:
             response = "I understand. "
    
        # After natural response, gently redirect based on phase
        if current_phase == "info_gathering":
            if self.current_info_index < len(self.required_info):
                field_name, question = self.required_info[self.current_info_index]
                response += f"Now, {question.lower()}"
            else:
                response += "Let's continue with learning about your technical background."
        elif current_phase == "tech_stack":
            response += "Could you tell me about your technical skills and experience?"
        elif current_phase == "technical_questions":
            if self.current_question_index < len(self.current_questions):
                tech, question = self.current_questions[self.current_question_index]
                response += f"Let's get back to our technical discussion: {question}"
    
        return response



    
    
    def _handle_tech_stack(self, user_message: str) -> str:
        """Handle tech stack declaration phase."""
        # Parse tech stack
        tech_stack = self.data_handler.parse_tech_stack(user_message)
        self.candidate_data["tech_stack"] = tech_stack

        if not tech_stack or not any(tech_stack.values()):
            return """I didn't catch any specific technologies from your response. Could you please list some specific technologies you work with?

For example: "I work with Python, React, MySQL, and Docker" """

        # Generate technical questions
        experience_years = self.candidate_data.get("experience_years", 1)
        questions = self.question_generator.generate_questions(
            tech_stack, experience_years
        )

        if not questions:
            # Skip to closing if no questions generated
            self.phase = ConversationPhase.CLOSING
            self._reset_natural_conversation_counter()
            return self._generate_closing_message()

        self.current_questions = questions
        self.current_question_index = 0
        self.phase = ConversationPhase.TECHNICAL_QUESTIONS
        self._reset_natural_conversation_counter()
        self.candidate_data["interview_responses"] = {}

        # Format tech stack summary
        tech_summary = self._format_tech_stack(tech_stack)

        return f"""Great! I can see you have experience with:

{tech_summary}

Now I'll ask you a few technical questions to better understand your expertise. Let's start with the first question:

**{self.current_questions[0][1]}**"""

    def _handle_technical_questions(self, user_message: str) -> str:
        """Handle technical questions phase."""
        if self.current_question_index < len(self.current_questions):
            # Store the answer
            tech, question = self.current_questions[self.current_question_index]
            self.candidate_data["interview_responses"][
                f"{tech}_{self.current_question_index}"
            ] = {"question": question, "answer": user_message, "technology": tech}

            # Move to next question
            self.current_question_index += 1

            if self.current_question_index < len(self.current_questions):
                next_tech, next_question = self.current_questions[
                    self.current_question_index
                ]

                # Provide brief feedback and ask next question
                feedback = self._generate_brief_feedback(user_message)
                return f"""{feedback}

**Next question about {next_tech}:**
{next_question}"""
            else:
                # All questions completed
                self.phase = ConversationPhase.CLOSING
                self._reset_natural_conversation_counter()
                return f"""Thank you for your detailed responses! 

{self._generate_closing_message()}"""

        return "Let me wrap up our conversation..."

    def _handle_closing(self, user_message: str) -> str:
        """Handle closing phase."""
        self.phase = ConversationPhase.ENDED
        self._reset_natural_conversation_counter()
        return "Thank you for taking the time to speak with us today. Have a great day!"

    def _handle_conversation_end(self) -> str:
        """Handle conversation ending."""
        self.phase = ConversationPhase.ENDED
        self._reset_natural_conversation_counter()
        return """Thank you for your time today! 

Your information has been recorded and our team will review it shortly. If you're a good fit for any of our current opportunities, we'll be in touch within the next few days.

Have a great day!"""

    def _format_tech_stack(self, tech_stack: Dict[str, List[str]]) -> str:
        """Format tech stack for display."""
        formatted = []
        for category, technologies in tech_stack.items():
            if technologies:
                formatted.append(f"• **{category}**: {', '.join(technologies)}")
        return "\n".join(formatted)

    def _generate_brief_feedback(self, answer: str) -> str:
        """Generate brief encouraging feedback."""
        feedback_options = [
            "Thank you for that explanation.",
            "I appreciate the detailed response.",
            "That's helpful to understand your experience.",
            "Good insights on that topic.",
            "Thanks for sharing your perspective.",
        ]

        # Simple logic based on answer length
        if len(answer.split()) > 30:
            return "Thank you for the detailed explanation."
        elif len(answer.split()) > 10:
            return "I appreciate that response."
        else:
            return "Thank you."

    def _generate_closing_message(self) -> str:
        """Generate closing message."""
        completion = self.data_handler.get_completion_percentage(self.candidate_data)

        return f"""That completes our initial screening process! 

Here's what happens next:
• Our team will review your information and responses
• If there's a good match with our current openings, we'll contact you within 2-3 business days
• You may be invited for a more detailed technical interview

Thank you for your time and interest in opportunities with TalentScout. We appreciate you taking the time to speak with us today!

Is there anything else you'd like to know about our process?"""

    def get_conversation_summary(self) -> Dict:
        """Get summary of the conversation for debugging."""
        return {
            "phase": self.phase.value,
            "candidate_data": self.data_handler.sanitize_data(self.candidate_data),
            "questions_asked": len(self.current_questions),
            "questions_answered": self.current_question_index,
            "completion_percentage": self.data_handler.get_completion_percentage(
                self.candidate_data
            ),
        }
    
    def _reset_natural_conversation_counter(self):
        """Reset natural conversation counter when moving to new phase."""
        self.natural_conversation_count = 0




    def reset_conversation(self):
        """Reset conversation state for new session."""
        self.phase = ConversationPhase.GREETING
        self.candidate_data = {}
        self.current_questions = []
        self.current_question_index = 0
        self.conversation_history = []
        self.current_info_index = 0
        # Reset duplicate handling state
        self.pending_duplicate_check = False
        self.pending_field_name = None
        self.pending_field_value = None
        # Reset natural conversation tracking
        self.natural_conversation_count = 0
        self.last_redirect_attempt = 0
