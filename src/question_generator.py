"""Technical question generation based on candidate's tech stack."""

from typing import Dict, List, Tuple
import random

class QuestionGenerator:
    """Generates technical questions based on tech stack and experience level."""
    
    def __init__(self):
        self.question_bank = self._initialize_question_bank()
    
    def _initialize_question_bank(self) -> Dict:
        """Initialize the question bank with various technologies."""
        return {
            'programming_languages': {
                'python': {
                    'junior': [
                        "What are the main differences between lists and tuples in Python?",
                        "How do you handle exceptions in Python? Can you give an example?",
                        "Explain what list comprehensions are and provide a simple example."
                    ],
                    'mid': [
                        "How would you implement a decorator in Python? What are some use cases?",
                        "Explain the difference between __str__ and __repr__ methods in Python classes.",
                        "How does Python's GIL (Global Interpreter Lock) affect multithreading?"
                    ],
                    'senior': [
                        "How would you optimize a Python application for better performance?",
                        "Explain metaclasses in Python and when you might use them.",
                        "How would you implement a memory-efficient solution for processing large datasets?"
                    ]
                },
                'javascript': {
                    'junior': [
                        "What's the difference between var, let, and const in JavaScript?",
                        "How do you handle asynchronous operations in JavaScript?",
                        "Explain what closures are in JavaScript with an example."
                    ],
                    'mid': [
                        "How does prototypal inheritance work in JavaScript?",
                        "What are Promises and how do they differ from callbacks?",
                        "Explain event bubbling and event capturing in the DOM."
                    ],
                    'senior': [
                        "How would you implement a custom Promise from scratch?",
                        "Explain the event loop in JavaScript and how it handles asynchronous operations.",
                        "How would you optimize JavaScript code for better performance?"
                    ]
                },
                'java': {
                    'junior': [
                        "What's the difference between abstract classes and interfaces in Java?",
                        "Explain the concept of inheritance in Java with an example.",
                        "What are the main principles of Object-Oriented Programming?"
                    ],
                    'mid': [
                        "How does garbage collection work in Java?",
                        "Explain the differences between ArrayList and LinkedList.",
                        "What are Java generics and why are they useful?"
                    ],
                    'senior': [
                        "How would you design a thread-safe singleton pattern in Java?",
                        "Explain the Java memory model and how it affects concurrent programming.",
                        "How would you optimize Java application performance?"
                    ]
                }
            },
            'frameworks': {
                'react': {
                    'junior': [
                        "What are React hooks and why were they introduced?",
                        "Explain the difference between functional and class components in React.",
                        "How do you pass data between parent and child components?"
                    ],
                    'mid': [
                        "How does the Virtual DOM work in React?",
                        "What are higher-order components (HOCs) and when would you use them?",
                        "Explain the React component lifecycle methods."
                    ],
                    'senior': [
                        "How would you optimize a React application's performance?",
                        "Explain React's reconciliation algorithm and how keys work.",
                        "How would you implement server-side rendering with React?"
                    ]
                },
                'django': {
                    'junior': [
                        "What is the MTV pattern in Django and how does it work?",
                        "How do you create and run database migrations in Django?",
                        "Explain what Django models are and how they relate to database tables."
                    ],
                    'mid': [
                        "How do Django's class-based views work and when would you use them?",
                        "Explain Django's ORM and how to optimize database queries.",
                        "How does Django's authentication system work?"
                    ],
                    'senior': [
                        "How would you scale a Django application for high traffic?",
                        "Explain Django's caching framework and different caching strategies.",
                        "How would you implement custom middleware in Django?"
                    ]
                }
            },
            'databases': {
                'mysql': {
                    'junior': [
                        "What's the difference between INNER JOIN and LEFT JOIN?",
                        "How do you create an index in MySQL and why would you use one?",
                        "Explain what primary keys and foreign keys are."
                    ],
                    'mid': [
                        "How would you optimize a slow MySQL query?",
                        "Explain the different MySQL storage engines and their use cases.",
                        "What are MySQL transactions and how do you use them?"
                    ],
                    'senior': [
                        "How would you design a database schema for high availability?",
                        "Explain MySQL replication and different replication strategies.",
                        "How would you handle database partitioning in MySQL?"
                    ]
                },
                'mongodb': {
                    'junior': [
                        "What are the main differences between SQL and NoSQL databases?",
                        "How do you query documents in MongoDB?",
                        "Explain what collections and documents are in MongoDB."
                    ],
                    'mid': [
                        "How does indexing work in MongoDB?",
                        "Explain MongoDB's aggregation pipeline with an example.",
                        "What are the advantages and disadvantages of using MongoDB?"
                    ],
                    'senior': [
                        "How would you design a MongoDB schema for optimal performance?",
                        "Explain MongoDB sharding and when you would use it.",
                        "How would you handle data consistency in a distributed MongoDB setup?"
                    ]
                }
            },
            'tools': {
                'docker': {
                    'junior': [
                        "What is Docker and what problems does it solve?",
                        "Explain the difference between Docker images and containers.",
                        "How do you create a simple Dockerfile?"
                    ],
                    'mid': [
                        "How do Docker volumes work and when would you use them?",
                        "Explain Docker networking and different network types.",
                        "How would you use Docker Compose for multi-container applications?"
                    ],
                    'senior': [
                        "How would you optimize Docker images for production use?",
                        "Explain Docker orchestration and container management strategies.",
                        "How would you implement a CI/CD pipeline with Docker?"
                    ]
                },
                'aws': {
                    'junior': [
                        "What are the main AWS services you've worked with?",
                        "Explain what EC2 instances are and their use cases.",
                        "How does AWS S3 work and what is it used for?"
                    ],
                    'mid': [
                        "How would you design a scalable architecture on AWS?",
                        "Explain AWS Lambda and when you would use serverless functions.",
                        "How does AWS RDS differ from running your own database?"
                    ],
                    'senior': [
                        "How would you implement a highly available system on AWS?",
                        "Explain AWS security best practices and IAM policies.",
                        "How would you optimize AWS costs for a large-scale application?"
                    ]
                }
            }
        }
    
    def generate_questions(self, tech_stack: Dict[str, List[str]], experience_years: int) -> List[Tuple[str, str]]:
        """Generate technical questions based on tech stack and experience."""
        experience_level = self._get_experience_level(experience_years)
        questions = []
        
        for category, technologies in tech_stack.items():
            for tech in technologies:
                tech_questions = self._get_questions_for_technology(tech.lower(), experience_level)
                if tech_questions:
                    # Select 2-3 random questions for each technology
                    selected = random.sample(tech_questions, min(3, len(tech_questions)))
                    for question in selected:
                        questions.append((tech, question))
        
        return questions
    
    def _get_experience_level(self, years: int) -> str:
        """Determine experience level based on years."""
        if years < 2:
            return 'junior'
        elif years < 5:
            return 'mid'
        else:
            return 'senior'
    
    def _get_questions_for_technology(self, technology: str, level: str) -> List[str]:
        """Get questions for a specific technology and level."""
        # Check programming languages
        if technology in self.question_bank['programming_languages']:
            return self.question_bank['programming_languages'][technology].get(level, [])
        
        # Check frameworks
        if technology in self.question_bank['frameworks']:
            return self.question_bank['frameworks'][technology].get(level, [])
        
        # Check databases
        if technology in self.question_bank['databases']:
            return self.question_bank['databases'][technology].get(level, [])
        
        # Check tools
        if technology in self.question_bank['tools']:
            return self.question_bank['tools'][technology].get(level, [])
        
        # Return generic questions if technology not found
        return self._get_generic_questions(technology, level)
    
    def _get_generic_questions(self, technology: str, level: str) -> List[str]:
        """Generate generic questions for unknown technologies."""
        base_questions = {
            'junior': [
                f"Can you explain what {technology} is and what it's used for?",
                f"What are the main features or benefits of using {technology}?",
                f"Can you describe a simple project where you used {technology}?"
            ],
            'mid': [
                f"How does {technology} compare to similar technologies you've used?",
                f"What are some best practices when working with {technology}?",
                f"Can you describe a challenging problem you solved using {technology}?"
            ],
            'senior': [
                f"How would you architect a large-scale system using {technology}?",
                f"What are the performance considerations when using {technology}?",
                f"How would you mentor a junior developer learning {technology}?"
            ]
        }
        
        return base_questions.get(level, base_questions['junior'])
    
    def get_followup_questions(self, technology: str, previous_answer: str) -> List[str]:
        """Generate follow-up questions based on the candidate's answer."""
        followups = [
            f"Can you elaborate more on that aspect of {technology}?",
            f"Have you encountered any challenges with {technology} in real projects?",
            f"How would you explain {technology} to someone who's never used it?",
            "What would you do differently if you were to implement this again?",
            "Can you think of any alternative approaches to solve this problem?"
        ]
        
        return random.sample(followups, 2)
    
    def evaluate_answer_complexity(self, answer: str) -> str:
        """Simple evaluation of answer complexity."""
        word_count = len(answer.split())
        
        if word_count < 10:
            return "brief"
        elif word_count < 50:
            return "moderate"
        else:
            return "detailed"